#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Export GitLab MR data for AI review:
- diffs (unified diff per file)
- comments (discussions/notes)
Output: ./out/mr/<MR>__iid_<iid>.mr.json

Usage:
  python scripts/gitlab_export_mr.py
  python scripts/gitlab_export_mr.py --mr-url "https://.../-/merge_requests/17"
"""

import argparse
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
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

def sanitize_filename(name: str, max_len: int = 150) -> str:
    name = (name or "").strip() or "output"
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    return (name[:max_len].rstrip() if len(name) > max_len else name) or "output"

def build_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
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

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        return self.session.get(self._url(path), headers=self._headers(), params=params, timeout=self.timeout)

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        r = self.get(path, params=params)
        if r.status_code >= 400:
            raise GitLabAPIError(f"GET {r.url} -> {r.status_code}\n{r.text[:2000]}")
        return r.json() if r.text.strip() else None

    def get_all_pages(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        items: List[Any] = []
        page = 1
        params = dict(params or {})
        params.setdefault("per_page", 100)
        while True:
            params["page"] = page
            r = self.get(path, params=params)
            if r.status_code >= 400:
                raise GitLabAPIError(f"GET {r.url} -> {r.status_code}\n{r.text[:2000]}")
            data = r.json() if r.text.strip() else []
            if isinstance(data, list):
                items.extend(data)
            else:
                return items + [data]
            nxt = r.headers.get("X-Next-Page")
            if not nxt:
                break
            page = int(nxt)
        return items

def export_one_mr(gl: GitLabClient, project_path: str, iid: int, include_system_notes: bool) -> Dict[str, Any]:
    project_enc = encode_project(project_path)

    mr = gl.get_json(f"/projects/{project_enc}/merge_requests/{iid}") or {}
    changes_obj = gl.get_json(f"/projects/{project_enc}/merge_requests/{iid}/changes") or {}
    changes = changes_obj.get("changes", []) if isinstance(changes_obj, dict) else []

    diffs: List[Dict[str, Any]] = []
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        diffs.append({
            "old_path": ch.get("old_path"),
            "new_path": ch.get("new_path"),
            "new_file": ch.get("new_file"),
            "renamed_file": ch.get("renamed_file"),
            "deleted_file": ch.get("deleted_file"),
            "diff": ch.get("diff"),
        })

    discussions = gl.get_all_pages(f"/projects/{project_enc}/merge_requests/{iid}/discussions")

    comments: List[Dict[str, Any]] = []
    for d in discussions:
        if not isinstance(d, dict):
            continue
        discussion_id = d.get("id")
        for n in (d.get("notes") or []):
            if not isinstance(n, dict):
                continue
            if (not include_system_notes) and n.get("system") is True:
                continue
            author = n.get("author") or {}
            comments.append({
                "discussion_id": discussion_id,
                "note_id": n.get("id"),
                "created_at": n.get("created_at"),
                "updated_at": n.get("updated_at"),
                "author": {
                    "id": author.get("id"),
                    "name": author.get("name"),
                    "username": author.get("username"),
                    "web_url": author.get("web_url"),
                },
                "body": n.get("body"),
                "position": n.get("position"),
                "resolved": n.get("resolved"),
                "system": n.get("system"),
                "note_url": n.get("url"),
            })

    payload = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mr": {
            "project_path": project_path,
            "iid": iid,
            "title": (mr.get("title") or "").strip(),
            "web_url": mr.get("web_url"),
            "state": mr.get("state"),
            "source_branch": mr.get("source_branch"),
            "target_branch": mr.get("target_branch"),
            "diff_refs": mr.get("diff_refs"),
        },
        "diffs": diffs,
        "comments": comments,
        "counts": {"diff_files": len(diffs), "comments": len(comments)},
    }
    return payload

import datetime

def main() -> int:
    ap = argparse.ArgumentParser(description="Export GitLab MR (diffs + comments) for AI review.")
    ap.add_argument("--mr-url", help="Optional single MR URL. If omitted, uses config.MR_URLS.")
    args = ap.parse_args()

    base_url = str(getattr(config, "GITLAB_BASE_URL", "")).strip()
    token = str(getattr(config, "GITLAB_TOKEN", "")).strip()
    out_dir = str(getattr(config, "OUT_DIR", "./out")).strip()
    include_system = bool(getattr(config, "INCLUDE_SYSTEM_NOTES", False))
    mr_urls = [args.mr_url] if args.mr_url else list(getattr(config, "MR_URLS", []) or [])

    if not base_url or not token:
        print("ERROR: config.py の GITLAB_BASE_URL / GITLAB_TOKEN を設定してください。", file=sys.stderr)
        return 2
    if not mr_urls:
        print("ERROR: MR URL がありません。config.py の MR_URLS を設定してください。", file=sys.stderr)
        return 2

    gl = GitLabClient(base_url=base_url, token=token, session=build_session())

    os.makedirs(os.path.join(out_dir, "mr"), exist_ok=True)

    for mr_url in mr_urls:
        mr_base, project_path, iid = parse_mr_url(mr_url)
        if mr_base.rstrip("/") != base_url.rstrip("/"):
            print(f"ERROR: host mismatch: {mr_url}", file=sys.stderr)
            continue

        payload = export_one_mr(gl, project_path, iid, include_system)
        title = sanitize_filename(payload["mr"].get("title") or payload["mr"].get("source_branch") or f"mr_{iid}")
        out_path = os.path.join(out_dir, "mr", f"{title}__iid_{iid}.mr.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"OK: wrote {out_path}")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as e:
        print(f"ERROR: network/request failed: {e}", file=sys.stderr)
        raise SystemExit(1)
