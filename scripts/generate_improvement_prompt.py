"""Collect debate histories and build an improvement request prompt for the next AI iteration.

Usage:
    python scripts/generate_improvement_prompt.py \
        --history-dir histories \
        [--output improvements.txt]

The script concatenates all files in the history directory and outputs a
single prompt that summarizes the context and asks an AI to propose
improvements. Files are embedded with fenced code blocks to preserve
formatting.
"""

import argparse
from pathlib import Path
import sys
from typing import Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an improvement prompt from debate histories.")
    parser.add_argument(
        "--history-dir",
        default="histories",
        help="Directory containing debate history files (default: histories)",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to write the resulting prompt; stdout is used when omitted.",
    )
    return parser.parse_args()


def load_histories(history_dir: Path) -> Dict[str, str]:
    if not history_dir.exists():
        sys.exit(f"History directory not found: {history_dir}")

    files = [path for path in sorted(history_dir.iterdir()) if path.is_file()]
    if not files:
        sys.exit(f"No history files found in: {history_dir}")

    return {file.name: file.read_text(encoding="utf-8") for file in files}


def build_prompt(histories: Dict[str, str]) -> str:
    sections = [
        "# 改善要求プロンプト",
        "以下は各ジャッジロールが残した勝負内容の履歴です。内容を踏まえて、次イテレーションで改善すべき点を提案してください。",
        "出力フォーマット:",
        "- 改善サマリー (箇条書き3〜7件)",
        "- 重大度: High/Medium/Low を各項目に付与",
        "- 推奨アクション: 具体的な手順や担当ロールを明記",
        "- 追加で確認すべき質問があれば列挙",
        "- 依存関係や前提に変更が必要な場合は明示",
        "",
        "## 履歴",
    ]

    for filename, content in histories.items():
        sections.append(f"### {filename}")
        sections.append("````markdown")
        sections.append(content.strip())
        sections.append("````")
        sections.append("")

    return "\n".join(sections).strip() + "\n"


def main() -> None:
    args = parse_args()
    history_dir = Path(args.history_dir)
    histories = load_histories(history_dir)
    prompt = build_prompt(histories)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(prompt, encoding="utf-8")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
