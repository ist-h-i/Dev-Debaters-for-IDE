# Metrics log guide
- Maintain one rolling metrics file per phase: `metrics/hearing.md`, `metrics/orchestration.md`, `metrics/plan.md`, `metrics/spec.md`, `metrics/code.md`, `metrics/doc.md`, and `metrics/review.md`. Append new entries to the appropriate phase file only; do not create dated metrics files or a single combined metrics log.
- Write each entry in English using the template below.

```
- Date: YYYY-MM-DD HH:mm
- Phase: hearing / orchestration / plan / spec / code / doc / review
- Winner: A (Score) / B (Score) — use a 0-100 scale where 100 is a perfect score.
- Loser Improvement Point: Output a concise one-sentence improvement point.
```
