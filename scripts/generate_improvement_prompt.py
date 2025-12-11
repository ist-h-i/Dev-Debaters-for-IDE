"""Collect the metrics log and build an improvement request prompt for the next AI iteration.

Usage:
    python scripts/generate_improvement_prompt.py \
        --metrics-log metrics/log.md \
        [--review-requirements prompts/review_requirements.md] \
        [--output improvements.txt]

The script embeds the metrics log into a single prompt that summarizes the
context and asks an AI to propose improvements using the metrics output format.
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an improvement prompt from the metrics log.")
    parser.add_argument(
        "--metrics-log",
        default="metrics/log.md",
        help="Path to the metrics log file (default: metrics/log.md)",
    )
    parser.add_argument(
        "--output",
        help="Optional file path to write the resulting prompt; stdout is used when omitted.",
    )
    parser.add_argument(
        "--review-requirements",
        default="prompts/review_requirements.md",
        help=(
            "Path to the review requirements file to embed (default: prompts/review_requirements.md). "
            "Omit or leave empty to skip."
        ),
    )
    return parser.parse_args()


def load_metrics_log(metrics_log: Path) -> str:
    if not metrics_log.exists():
        sys.exit(f"Metrics log not found: {metrics_log}")

    content = metrics_log.read_text(encoding="utf-8").strip()
    if not content:
        sys.exit(f"Metrics log is empty: {metrics_log}")

    return content


def build_prompt(metrics_log: str, review_requirements: Optional[str]) -> str:
    sections = [
        "# Improvement request prompt",
        "Below is the cumulative metrics log. Using this context, propose what to improve in the next iteration.",
        "Output format:",
        "## Issue: <short title>",
        "- Date: YYYY-MM-DD HH:mm",
        "- Phases: hearing / orchestration / plan / spec / code / doc / review (keep only completed ones)",
        "- Winner: A (Score) / B (Score)",
        "- Loser 改善ポイント: 一文で簡潔に改善ポイントを出力する",
        "",
    ]

    sections.append("## Review requirements (persisted inputs)")
    sections.append(
        "Embed the latest review-specific requirements below to ensure downstream prompts reflect current guardrails."
    )
    if review_requirements:
        sections.append("````markdown")
        sections.append(review_requirements)
        sections.append("````")
    else:
        sections.append("(none provided)")
    sections.append("")

    sections.append("## Metrics log")

    sections.append("````markdown")
    sections.append(metrics_log)
    sections.append("````")

    return "\n".join(sections).strip() + "\n"


def main() -> None:
    args = parse_args()
    metrics_log = Path(args.metrics_log)
    review_requirements_path = Path(args.review_requirements) if args.review_requirements else None
    log_content = load_metrics_log(metrics_log)
    review_requirements_content = ""

    if review_requirements_path:
        if review_requirements_path.exists() and review_requirements_path.is_file():
            review_requirements_content = review_requirements_path.read_text(encoding="utf-8").strip()
        elif review_requirements_path.exists():
            sys.exit(f"Review requirements path is not a file: {review_requirements_path}")

    prompt = build_prompt(log_content, review_requirements_content)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(prompt, encoding="utf-8")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
