#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Build a single prompt pack for 'coding rules update' by injecting:
- existing coding rules JSON
- fetched MR comments JSON

Output: ./in/compiled/<name>.rules_update.prompt.md

Usage:
  python scripts/build_rules_update_prompt_pack.py --comments-json ./out/comments/foo__iid_17.comments.json
"""

import argparse
import pathlib

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

def read_text(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser(description="Build prompt pack for coding rules merge/update.")
    ap.add_argument("--comments-json", required=True, help="Path to comments json (from gitlab_fetch_mr_comments.py)")
    ap.add_argument("--out-dir", default="./in/compiled", help="Output directory")
    args = ap.parse_args()

    in_dir = HERE / "in" / "rules_update"
    template = read_text(in_dir / "prompt_pack_template.md")
    system_prompt = read_text(in_dir / "system_prompt.md")
    user_prompt = read_text(in_dir / "user_prompt.md")
    update_req = read_text(in_dir / "update_request.md")

    rules_file = pathlib.Path(str(getattr(config, "CODING_RULES_FILE", "./rules/coding_rules.json")))
    if not rules_file.exists():
        raise FileNotFoundError(f"CODING_RULES_FILE not found: {rules_file}")

    comments_file = pathlib.Path(args.comments_json)
    if not comments_file.exists():
        raise FileNotFoundError(f"comments json not found: {comments_file}")

    compiled = template
    compiled = compiled.replace("{{SYSTEM_PROMPT}}", system_prompt)
    compiled = compiled.replace("{{USER_PROMPT}}", user_prompt)
    compiled = compiled.replace("{{UPDATE_REQUEST}}", update_req)
    compiled = compiled.replace("{{CODING_RULES_JSON}}", read_text(rules_file))
    compiled = compiled.replace("{{MR_COMMENTS_JSON}}", read_text(comments_file))

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / (comments_file.stem + ".rules_update.prompt.md")
    out_path.write_text(compiled, encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
