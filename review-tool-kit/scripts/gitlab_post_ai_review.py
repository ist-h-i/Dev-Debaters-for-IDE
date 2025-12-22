#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Post AI review result JSON to GitLab MR:
- Overall MR note (single)
- Inline discussions with position (file+line) for changed code

Input: AI review JSON (mr_overall + inline_comments)
Usage:
  python scripts/gitlab_post_ai_review.py --mr-url "https://.../-/merge_requests/17" --review-json "./review_out/foo.review.json"
"""

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import importlib.util
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
CONFIG_FILE = HERE / "config.py"
TEMPLATE_FILE = HERE / "config.template.py"

def load_config_module():
    if not CONFIG_FILE.exists():
        if TEMPLATE_FILE.exists():
            shutil.copyfile(TEMPLATE_FILE, CONFIG_FILE)
            print("ERROR: config.py が存在しなかったため config.template.py から生成しました。", file=sys.stderr)
            print("config.py を編集して GITLAB_TOKEN / MR_URLS 等を設定後、再実行してください。", file=sys.stderr)
            print(f"生成先: {CONFIG_FILE}", file=sys.stderr)
            sys.exit(2)
        raise RuntimeError("config.py / config.template.py が見つかりません。")
    spec = importlib.util.spec_from_file_location("config", str(CONFIG_FILE))
    if spec is None or spec.loader is None:
        raise RuntimeError("config.py の読み込みに失敗しました。")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module

config = load_config_module()

MR_URL_RE = re.compile(r"^/(?P<project>.+)/-/merge_requests/(?P<iid>\d+)(?:/.*)?$")

def parse_mr_url(mr_url: str) -> Tuple[str, str, int]:
    u = urlparse(mr_url.strip())
    if not u.scheme or not u.netloc:
        raise ValueError(f"Invalid URL: {mr_url}")
    base_url = f"{u.scheme}://{u.netloc}"
    m = MR_URL_RE.match(u.path)
    if not m:
        raise ValueError(f"Unsupported MR URL format: {mr_url}")
    return base_url, m.group("project"), int(m.group("iid"))

def is_int_string(s: str) -> bool:
    try:
        int(s)
        return True
    except Exception:
        return False

def encode_project(project: str) -> str:
    return project if is_int_string(project) else quote_plus(project)

def build_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

class GitLabAPIError(RuntimeError):
    pass

@dataclass
class GitLabClient:
    base_url: str
    token: str
    session: requests.Session
    timeout: int = 30

    def _headers(self) -> Dict[str, str]:
        return {"PRIVATE-TOKEN": self.token, "Accept": "application/json"}

    def _url(self, path: str) -> str:
        return self.base_url.rstrip("/") + "/api/v4" + path

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        r = self.session.get(self._url(path), headers=self._headers(), params=params, timeout=self.timeout)
        if r.status_code >= 400:
            raise GitLabAPIError(f"GET {r.url} -> {r.status_code}\n{r.text[:2000]}")
        return r.json() if r.text.strip() else None

    def post_json(self, path: str, payload: Dict[str, Any]) -> Any:
        r = self.session.post(self._url(path), headers=self._headers(), json=payload, timeout=self.timeout)
        if r.status_code >= 400:
            raise GitLabAPIError(f"POST {r.url} -> {r.status_code}\n{r.text[:2000]}")
        return r.json() if r.text.strip() else None

def format_overall_comment(overall: Dict[str, Any]) -> str:
    status = (overall.get("status") or "").strip() or "指摘あり"
    changes = (overall.get("changes_summary") or "").strip() or "（記載なし）"
    risk = (overall.get("risk_impact") or "").strip() or "（記載なし）"
    return (
        "【By AI reviewer】\n"
        f"【ステータス（{status}）】\n"
        f"【変更内容】{changes}\n"
        f"【影響範囲・リスク】{risk}\n"
    )

def format_inline_comment(c: Dict[str, Any]) -> str:
    sev = (c.get("severity") or "").strip() or "解説"
    detail = (c.get("detail") or "").strip() or "【詳細】（記載なし）"
    fix = (c.get("fix_example") or "").strip() or "【修正例】（記載なし）"
    impact = (c.get("impact") or "").strip() or "【影響範囲】（記載なし）"
    return (
        "【By AI reviewer】\n"
        f"【重要度（{sev}）】\n"
        f"{detail}\n"
        f"{fix}\n"
        f"{impact}\n"
    )

def main() -> int:
    ap = argparse.ArgumentParser(description="Post AI review JSON to GitLab MR (overall note + inline discussions).")
    ap.add_argument("--mr-url", required=True, help="MR URL")
    ap.add_argument("--review-json", required=True, help="AI review JSON path")
    ap.add_argument("--dry-run", action="store_true", help="Print only, do not post")
    args = ap.parse_args()

    base_url = str(getattr(config, "GITLAB_BASE_URL", "")).strip()
    token = str(getattr(config, "GITLAB_TOKEN", "")).strip()
    if not base_url or not token:
        print("ERROR: config.py の GITLAB_BASE_URL / GITLAB_TOKEN を設定してください。", file=sys.stderr)
        return 2

    mr_base, project_path, iid = parse_mr_url(args.mr_url)
    if mr_base.rstrip("/") != base_url.rstrip("/"):
        print(f"ERROR: MR URL host({mr_base}) と config.GITLAB_BASE_URL({base_url}) が不一致です。", file=sys.stderr)
        return 2

    review = json.loads(pathlib.Path(args.review_json).read_text(encoding="utf-8"))
    overall = review.get("mr_overall") or {}
    inline_comments = review.get("inline_comments") or []

    gl = GitLabClient(base_url=base_url, token=token, session=build_session())
    project_enc = encode_project(project_path)

    mr = gl.get_json(f"/projects/{project_enc}/merge_requests/{iid}")
    if not isinstance(mr, dict):
        print("ERROR: MR metadata fetch failed.", file=sys.stderr)
        return 1

    diff_refs = mr.get("diff_refs") or {}
    base_sha = diff_refs.get("base_sha")
    start_sha = diff_refs.get("start_sha")
    head_sha = diff_refs.get("head_sha")
    if not (base_sha and start_sha and head_sha):
        print("ERROR: MR diff_refs missing (base_sha/start_sha/head_sha).", file=sys.stderr)
        return 1

    # Overall note
    overall_body = format_overall_comment(overall)
    if args.dry_run:
        print("---- Overall ----")
        print(overall_body)
    else:
        gl.post_json(f"/projects/{project_enc}/merge_requests/{iid}/notes", {"body": overall_body})
        print("OK: posted overall note")

    # Inline discussions
    for idx, c in enumerate(inline_comments, start=1):
        path = (c.get("path") or "").strip()
        side = (c.get("side") or "new").strip()
        line = c.get("line")

        if not path or not isinstance(line, int) or line <= 0:
            print(f"WARN: skip inline[{idx}] invalid path/line", file=sys.stderr)
            continue

        position: Dict[str, Any] = {
            "position_type": "text",
            "base_sha": base_sha,
            "start_sha": start_sha,
            "head_sha": head_sha,
        }
        if side == "old":
            position["old_path"] = path
            position["old_line"] = line
        else:
            position["new_path"] = path
            position["new_line"] = line

        body = format_inline_comment(c)
        if args.dry_run:
            print(f"---- Inline {idx} ----")
            print(json.dumps(position, ensure_ascii=False))
            print(body)
        else:
            gl.post_json(f"/projects/{project_enc}/merge_requests/{iid}/discussions", {"body": body, "position": position})
            print(f"OK: posted inline {idx}")

    return 0

if __name__ == "__main__":
    import pathlib
    try:
        raise SystemExit(main())
    except requests.RequestException as e:
        print(f"ERROR: network/request failed: {e}", file=sys.stderr)
        raise SystemExit(1)
    except GitLabAPIError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
