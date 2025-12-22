#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitLab MR Exporter (Batch by MR URL list)
- Read MR URLs from config.py (generated from config.template.py)
- For each MR URL:
  - Fetch MR metadata
  - Fetch MR diffs (changes) and parse unified diff for best-effort code context
  - Fetch MR discussions/notes
  - Export one JSON per MR
- Also writes a batch summary JSON: batch_export_summary.json

Requirements:
  pip install requests

Run:
  python gitlab_mr_export.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import pathlib
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------------------
# Config loader (template operation)
# ---------------------------------------------------------------------

HERE = pathlib.Path(__file__).resolve().parent
CONFIG_FILE = HERE / "config.py"
TEMPLATE_FILE = HERE / "config.template.py"


def load_config_module():
    """
    Load config.py.
    If missing, auto-generate from config.template.py and exit with instructions.
    """
    if not CONFIG_FILE.exists():
        if TEMPLATE_FILE.exists():
            shutil.copyfile(TEMPLATE_FILE, CONFIG_FILE)
            print("ERROR: config.py が存在しなかったため、config.template.py から生成しました。", file=sys.stderr)
            print("次に config.py を編集して、GITLAB_TOKEN / MR_URLS 等を設定してから再実行してください。", file=sys.stderr)
            print(f"生成先: {CONFIG_FILE}", file=sys.stderr)
            sys.exit(2)
        else:
            print("ERROR: config.py / config.template.py が見つかりません。", file=sys.stderr)
            sys.exit(2)

    # Import config.py from this directory explicitly
    import importlib.util

    spec = importlib.util.spec_from_file_location("config", str(CONFIG_FILE))
    if spec is None or spec.loader is None:
        print("ERROR: config.py の読み込みに失敗しました（import spec が作れません）。", file=sys.stderr)
        sys.exit(2)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


config = load_config_module()


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sanitize_filename(name: str, max_len: int = 150) -> str:
    if not name:
        return "output"
    name = name.strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)      # control chars
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)      # forbidden on Windows
    name = re.sub(r"\s+", " ", name).strip()
    name = name.rstrip(". ")
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "output"

def is_int_string(s: str) -> bool:
    try:
        int(s)
        return True
    except Exception:
        return False

def encode_project(project: str) -> str:
    """
    project can be numeric id "123" or path "group/subgroup/repo".
    GitLab API allows both. Path must be URL-encoded.
    """
    if is_int_string(project):
        return project
    return quote_plus(project)

def build_session(timeout_sec: int = 30) -> Tuple[requests.Session, int]:
    session = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session, timeout_sec


class GitLabAPIError(RuntimeError):
    pass


# ---------------------------------------------------------------------
# MR URL parsing
# ---------------------------------------------------------------------

MR_URL_RE = re.compile(r"^/(?P<project>.+)/-/merge_requests/(?P<iid>\d+)(?:/.*)?$")

def parse_mr_url(mr_url: str) -> Tuple[str, str, int]:
    """
    Parse MR URL:
      https://<host>/<project_path>/-/merge_requests/<iid>
    Returns:
      (base_url, project_path, iid)
    """
    u = urlparse(mr_url.strip())
    if not u.scheme or not u.netloc:
        raise ValueError(f"Invalid URL (scheme/host missing): {mr_url}")
    base_url = f"{u.scheme}://{u.netloc}"
    m = MR_URL_RE.match(u.path)
    if not m:
        raise ValueError(f"Unsupported MR URL path format: {mr_url}")
    project_path = m.group("project")
    iid = int(m.group("iid"))
    return base_url, project_path, iid


# ---------------------------------------------------------------------
# GitLab Client
# ---------------------------------------------------------------------

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
        resp = self.get(path, params=params)
        if resp.status_code >= 400:
            raise GitLabAPIError(
                f"GitLab API error {resp.status_code} for GET {resp.url}\nResponse: {resp.text[:2000]}"
            )
        return resp.json() if resp.text.strip() else None

    def get_all_pages(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        items: List[Any] = []
        page = 1
        per_page = 100
        params = dict(params or {})
        params.setdefault("per_page", per_page)

        while True:
            params["page"] = page
            resp = self.get(path, params=params)
            if resp.status_code >= 400:
                raise GitLabAPIError(
                    f"GitLab API error {resp.status_code} for GET {resp.url}\nResponse: {resp.text[:2000]}"
                )
            data = resp.json() if resp.text.strip() else []
            if isinstance(data, list):
                items.extend(data)
            else:
                return items + [data]

            next_page = resp.headers.get("X-Next-Page")
            if not next_page:
                break
            page = int(next_page)

        return items


# ---------------------------------------------------------------------
# Unified diff parsing for best-effort context
# ---------------------------------------------------------------------

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def build_line_maps_from_diff(diff_text: str) -> Tuple[Dict[int, str], Dict[int, str]]:
    new_map: Dict[int, str] = {}
    old_map: Dict[int, str] = {}

    old_ln: Optional[int] = None
    new_ln: Optional[int] = None

    for raw in diff_text.splitlines():
        if raw.startswith("+++ ") or raw.startswith("--- "):
            continue

        m = HUNK_RE.match(raw)
        if m:
            old_ln = int(m.group(1))
            new_ln = int(m.group(3))
            continue

        if old_ln is None or new_ln is None:
            continue

        if raw.startswith("\\ No newline at end of file"):
            continue

        if raw.startswith(" "):
            content = raw[1:]
            old_map[old_ln] = content
            new_map[new_ln] = content
            old_ln += 1
            new_ln += 1
        elif raw.startswith("+"):
            content = raw[1:]
            new_map[new_ln] = content
            new_ln += 1
        elif raw.startswith("-"):
            content = raw[1:]
            old_map[old_ln] = content
            old_ln += 1

    return new_map, old_map

def extract_context(line_map: Dict[int, str], target_line: int, radius: int = 3) -> Optional[Dict[str, Any]]:
    if not line_map or target_line not in line_map:
        return None

    start = target_line - radius
    end = target_line + radius
    lines: List[Dict[str, Any]] = []
    for ln in range(start, end + 1):
        if ln in line_map:
            lines.append({"line": ln, "text": line_map[ln]})

    return {"target_line": target_line, "radius": radius, "lines": lines}


# ---------------------------------------------------------------------
# Export one MR
# ---------------------------------------------------------------------

def export_one_mr(
    gl: GitLabClient,
    project_path: str,
    mr_iid: int,
    out_dir: str,
    context_radius: int,
    include_system_notes: bool,
) -> Dict[str, Any]:
    """
    Export one MR and write JSON file.
    Returns a result dict for batch summary.
    """
    project_enc = encode_project(project_path)

    # 1) MR metadata
    mr = gl.get_json(f"/projects/{project_enc}/merge_requests/{mr_iid}")
    if not isinstance(mr, dict):
        raise GitLabAPIError("Unexpected MR response type.")

    title = (mr.get("title") or "").strip()
    source_branch = (mr.get("source_branch") or "").strip()

    # 2) Changes/diffs -> build per-file line maps
    changes_obj = gl.get_json(f"/projects/{project_enc}/merge_requests/{mr_iid}/changes")
    diffs = changes_obj.get("changes", []) if isinstance(changes_obj, dict) else []

    file_maps: Dict[str, Dict[str, Dict[int, str]]] = {}
    for ch in diffs:
        if not isinstance(ch, dict):
            continue
        new_path = ch.get("new_path") or ""
        old_path = ch.get("old_path") or ""
        diff_text = ch.get("diff") or ""
        if not diff_text:
            continue
        try:
            new_map, old_map = build_line_maps_from_diff(diff_text)
            key = new_path or old_path
            if key:
                file_maps[key] = {"new": new_map, "old": old_map}
        except Exception:
            continue

    # 3) Discussions/notes
    discussions = gl.get_all_pages(f"/projects/{project_enc}/merge_requests/{mr_iid}/discussions")

    out_discussions: List[Dict[str, Any]] = []
    note_count = 0

    for d in discussions:
        if not isinstance(d, dict):
            continue
        notes = d.get("notes") or []
        out_notes: List[Dict[str, Any]] = []

        for n in notes:
            if not isinstance(n, dict):
                continue
            if (not include_system_notes) and n.get("system") is True:
                continue

            position = n.get("position")
            pos_out: Optional[Dict[str, Any]] = None
            context_out: Optional[Dict[str, Any]] = None

            if isinstance(position, dict):
                new_path = position.get("new_path")
                old_path = position.get("old_path")
                new_line = position.get("new_line")
                old_line = position.get("old_line")

                pos_out = {
                    "position_type": position.get("position_type"),
                    "new_path": new_path,
                    "old_path": old_path,
                    "new_line": new_line,
                    "old_line": old_line,
                    "base_sha": position.get("base_sha"),
                    "start_sha": position.get("start_sha"),
                    "head_sha": position.get("head_sha"),
                }

                if new_path and isinstance(new_line, int) and new_path in file_maps:
                    context_out = extract_context(file_maps[new_path]["new"], new_line, radius=context_radius)
                elif old_path and isinstance(old_line, int) and old_path in file_maps:
                    context_out = extract_context(file_maps[old_path]["old"], old_line, radius=context_radius)

            author = n.get("author") or {}
            out_notes.append({
                "id": n.get("id"),
                "type": n.get("type"),
                "system": n.get("system"),
                "resolved": n.get("resolved"),
                "resolvable": n.get("resolvable"),
                "created_at": n.get("created_at"),
                "updated_at": n.get("updated_at"),
                "author": {
                    "id": author.get("id"),
                    "name": author.get("name"),
                    "username": author.get("username"),
                    "state": author.get("state"),
                    "web_url": author.get("web_url"),
                },
                "body": n.get("body"),
                "position": pos_out,
                "code_context": context_out,
                "note_url": n.get("url"),
            })
            note_count += 1

        if out_notes:
            out_discussions.append({
                "id": d.get("id"),
                "individual_note": d.get("individual_note"),
                "notes": out_notes,
            })

    payload: Dict[str, Any] = {
        "fetched_at": utc_now_iso(),
        "gitlab": {"base_url": gl.base_url, "project": project_path, "project_encoded": project_enc},
        "merge_request": {
            "iid": mr_iid,
            "id": mr.get("id"),
            "title": title,
            "state": mr.get("state"),
            "created_at": mr.get("created_at"),
            "updated_at": mr.get("updated_at"),
            "merged_at": mr.get("merged_at"),
            "source_branch": source_branch,
            "target_branch": mr.get("target_branch") or "",
            "web_url": mr.get("web_url") or "",
        },
        "export": {
            "include_system_notes": bool(include_system_notes),
            "context_radius": int(context_radius),
            "discussion_count": len(out_discussions),
            "note_count": note_count,
        },
        "discussions": out_discussions,
    }

    base_name_candidate = title or source_branch or f"mr_{mr_iid}"
    base_name = sanitize_filename(base_name_candidate)

    # タイトル重複対策（同名があり得るため IID を付与）
    out_name = f"{base_name}__iid_{mr_iid}.json"
    out_path = os.path.join(out_dir, out_name)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {
        "mr_url": mr.get("web_url") or "",
        "project": project_path,
        "iid": mr_iid,
        "title": title,
        "source_branch": source_branch,
        "output_file": out_path,
        "discussion_count": len(out_discussions),
        "note_count": note_count,
        "status": "ok",
    }


# ---------------------------------------------------------------------
# Main (batch)
# ---------------------------------------------------------------------

def main() -> int:
    base_url = str(getattr(config, "GITLAB_BASE_URL", "")).strip()
    token = str(getattr(config, "GITLAB_TOKEN", "")).strip()
    out_dir = str(getattr(config, "DEFAULT_OUT_DIR", "./out")).strip()
    context_radius = int(getattr(config, "DEFAULT_CONTEXT_RADIUS", 3))
    include_system_notes = bool(getattr(config, "INCLUDE_SYSTEM_NOTES", False))
    mr_urls = list(getattr(config, "MR_URLS", []) or [])

    if not base_url:
        print("ERROR: config.py の GITLAB_BASE_URL が未設定です。", file=sys.stderr)
        return 2
    if not token:
        print("ERROR: config.py の GITLAB_TOKEN が未設定です。", file=sys.stderr)
        return 2
    if not mr_urls:
        print("ERROR: config.py の MR_URLS が空です。少なくとも1件のMR URLを設定してください。", file=sys.stderr)
        return 2

    # One client for the configured base_url/token
    session, timeout = build_session()
    gl = GitLabClient(base_url=base_url, token=token, session=session, timeout=timeout)

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for mr_url in mr_urls:
        try:
            mr_base, project_path, iid = parse_mr_url(mr_url)

            # 安全策：MR URL のホストと config の base_url が一致しない場合は明示的に失敗させる
            if mr_base.rstrip("/") != base_url.rstrip("/"):
                raise ValueError(
                    f"MR URL のホスト({mr_base}) と config.GITLAB_BASE_URL({base_url}) が一致しません。"
                    "同一ホストに揃えるか、運用を分けてください。"
                )

            r = export_one_mr(
                gl=gl,
                project_path=project_path,
                mr_iid=iid,
                out_dir=out_dir,
                context_radius=context_radius,
                include_system_notes=include_system_notes,
            )
            results.append(r)
            print(f"OK: {r['output_file']}")
        except Exception as e:
            err = {"mr_url": mr_url, "status": "error", "error": str(e)}
            errors.append(err)
            print(f"ERROR: {mr_url}\n  {e}", file=sys.stderr)

    # Batch summary
    summary = {
        "fetched_at": utc_now_iso(),
        "gitlab": {"base_url": base_url},
        "export": {
            "out_dir": out_dir,
            "context_radius": context_radius,
            "include_system_notes": include_system_notes,
        },
        "results": results,
        "errors": errors,
        "counts": {"ok": len(results), "error": len(errors), "total": len(mr_urls)},
    }

    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, "batch_export_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"OK: wrote {summary_path}")
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.RequestException as e:
        print(f"ERROR: network/request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)
