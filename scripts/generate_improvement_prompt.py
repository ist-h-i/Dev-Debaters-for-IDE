"""Collect the metrics log and build an improvement request prompt for the next AI iteration.

Usage:
    python scripts/generate_improvement_prompt.py \
        --metrics-log metrics/log.md \
        [--output improvements.txt]

The script embeds the metrics log into a single prompt that summarizes the
context and asks an AI to propose improvements using the metrics output format.
"""

import argparse
from pathlib import Path
import sys

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
    return parser.parse_args()


def load_metrics_log(metrics_log: Path) -> str:
    if not metrics_log.exists():
        sys.exit(f"Metrics log not found: {metrics_log}")

    content = metrics_log.read_text(encoding="utf-8").strip()
    if not content:
        sys.exit(f"Metrics log is empty: {metrics_log}")

    return content


def build_prompt(metrics_log: str) -> str:
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
        "## Metrics log",
    ]

    sections.append("````markdown")
    sections.append(metrics_log)
    sections.append("````")

    return "\n".join(sections).strip() + "\n"


def main() -> None:
    args = parse_args()
    metrics_log = Path(args.metrics_log)
    log_content = load_metrics_log(metrics_log)
    prompt = build_prompt(log_content)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(prompt, encoding="utf-8")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
