#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Build a single prompt pack for MR review by injecting:
- system/user templates
- guidelines.md
- findings stock json
- MR export json

Output: ./in/compiled/<mr_stem>.mr_review.prompt.md

Usage:
  python scripts/build_mr_review_prompt_pack.py --mr-json ./out/mr/foo__iid_17.mr.json
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
    ap = argparse.ArgumentParser(description="Build prompt pack for MR review (guidelines + stock + MR json).")
    ap.add_argument("--mr-json", required=True, help="Path to MR export json (from gitlab_export_mr.py)")
    ap.add_argument("--out-dir", default="./in/compiled", help="Output directory")
    args = ap.parse_args()

    in_dir = HERE / "in" / "mr_review"
    template = read_text(in_dir / "prompt_pack_template.md")
    system_prompt = read_text(in_dir / "system_prompt.md")
    user_prompt = read_text(in_dir / "user_prompt.md")
    review_req = read_text(in_dir / "review_request.md")

    guidelines_file = pathlib.Path(str(getattr(config, "GUIDELINES_MD_FILE", "./in/guidelines.md")))
    # Use coding rules as the authoritative historical stock for MR review.
    stock_file = pathlib.Path(str(getattr(config, "CODING_RULES_FILE", "./rules/coding_rules.json")))
    mr_file = pathlib.Path(args.mr_json)

    if not guidelines_file.exists():
        raise FileNotFoundError(f"GUIDELINES_MD_FILE not found: {guidelines_file}")
    if not stock_file.exists():
        raise FileNotFoundError(f"CODING_RULES_FILE not found: {stock_file}")
    if not mr_file.exists():
        raise FileNotFoundError(f"MR json not found: {mr_file}")

    compiled = template
    compiled = compiled.replace("{{SYSTEM_PROMPT}}", system_prompt)
    compiled = compiled.replace("{{USER_PROMPT}}", user_prompt)

    rr = review_req
    rr = rr.replace("{{GUIDELINES_MD}}", read_text(guidelines_file))
    rr = rr.replace("{{CODING_RULES_JSON}}", read_text(stock_file))
    rr = rr.replace("{{MR_JSON}}", read_text(mr_file))

    compiled = compiled.replace("{{REVIEW_REQUEST}}", rr)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / (mr_file.stem + ".mr_review.prompt.md")
    out_path.write_text(compiled, encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
