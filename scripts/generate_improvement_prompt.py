"""Collect all metrics logs and review issues into a consolidated improvement prompt.

Usage:
    python scripts/generate_improvement_prompt.py \
        [--metrics-dir metrics] \
        [--review-issues metrics/review_issues.md] \
        [--output improvements.txt]

The script scans every metrics log file, identifies the losing role in each
entry, and gathers the corresponding improvement points. It then bundles these
role-specific improvements together with the accumulated review issues into a
single prompt that can be fed to the next iteration for refinement.
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an improvement prompt from all metrics logs and review issues."
    )
    parser.add_argument(
        "--metrics-dir",
        default="metrics",
        help="Directory containing metrics log files (default: metrics)",
    )
    parser.add_argument(
        "--review-issues",
        default="metrics/review_issues.md",
        help="Path to the review issues backlog (default: metrics/review_issues.md)",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to write the resulting prompt; stdout is used when omitted.",
    )
    return parser.parse_args()


def find_metrics_files(metrics_dir: Path) -> list[Path]:
    if not metrics_dir.exists():
        sys.exit(f"Metrics directory not found: {metrics_dir}")

    candidates = sorted(metrics_dir.glob("*.md"))
    return [
        path
        for path in candidates
        if path.name not in {"README.md", "review_issues.md"}
    ]


def load_review_issues(review_issues_path: Path) -> str:
    if not review_issues_path.exists():
        return ""

    if review_issues_path.is_file():
        return review_issues_path.read_text(encoding="utf-8").strip()

    sys.exit(f"Review issues path is not a file: {review_issues_path}")


def parse_entry_scores(line: str) -> Optional[str]:
    line = line.strip()
    if not line.lower().startswith("- winner:"):
        return None

    try:
        left, right = line.split(":", 1)[1].split("/")
        a_score = float(left.replace("A", "").replace("(", "").replace(")", "").strip())
        b_score = float(right.replace("B", "").replace("(", "").replace(")", "").strip())
    except Exception:
        return None

    if a_score == b_score:
        return "A and B"
    return "B" if a_score > b_score else "A"


def parse_metrics_entries(metrics_files: list[Path]) -> dict[str, list[str]]:
    role_improvements: dict[str, list[str]] = {}

    for file_path in metrics_files:
        content = file_path.read_text(encoding="utf-8")
        date: Optional[str] = None
        phase: Optional[str] = None
        winner_line: Optional[str] = None
        improvement_point: Optional[str] = None

        def flush_entry() -> None:
            nonlocal date, phase, winner_line, improvement_point
            if improvement_point:
                target_role = parse_entry_scores(winner_line or "") or "Unknown"
                label_parts = []
                if phase:
                    label_parts.append(f"Phase: {phase}")
                if date:
                    label_parts.append(f"Date: {date}")
                label = " | ".join(label_parts) if label_parts else "(no metadata)"
                text = f"{label} — {improvement_point}"
                role_improvements.setdefault(target_role, []).append(text)

            date = None
            phase = None
            winner_line = None
            improvement_point = None

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.lower().startswith("- date:"):
                date = line.split(":", 1)[1].strip()
            elif line.lower().startswith("- phase:"):
                phase = line.split(":", 1)[1].strip()
            elif line.lower().startswith("- winner:"):
                winner_line = line
            elif line.lower().startswith("- loser improvement point:"):
                improvement_point = line.split(":", 1)[1].strip()
            elif not line:
                flush_entry()

        flush_entry()

    return role_improvements


def build_prompt(role_improvements: dict[str, list[str]], review_issues: str) -> str:
    sections = [
        "# 改善用プロンプト",
        "以下の情報を踏まえて、該当ロールの改善策を検討してください。",
        "",
        "## レビュー指摘のバックログ",
    ]

    if review_issues:
        sections.append("````markdown")
        sections.append(review_issues)
        sections.append("````")
    else:
        sections.append("(review_issues.md に記載はありません)")

    sections.append("")
    sections.append("## ロール別の改善ポイント (メトリクスログより抽出)")

    if role_improvements:
        for role in sorted(role_improvements.keys()):
            sections.append(f"### Role {role}")
            for item in role_improvements[role]:
                sections.append(f"- {item}")
            sections.append("")
    else:
        sections.append("(メトリクスログから改善ポイントは抽出されませんでした)")

    return "\n".join(section for section in sections if section is not None).strip() + "\n"


def main() -> None:
    args = parse_args()
    metrics_dir = Path(args.metrics_dir)
    review_issues_path = Path(args.review_issues)

    metrics_files = find_metrics_files(metrics_dir)
    role_improvements = parse_metrics_entries(metrics_files)
    review_issues_content = load_review_issues(review_issues_path)

    prompt = build_prompt(role_improvements, review_issues_content)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(prompt, encoding="utf-8")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
