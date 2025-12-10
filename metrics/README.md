# Metrics log guide
- Append one entry per cycle (append-only).
- Keep one persistent log file `metrics/log.md`; do not split by day or issue so the full performance history stays in one place.
- Judges append the latest entry directly at phase completion (create the file if missing).

```
## Issue: <short title or link>
- Date: YYYY-MM-DD
- Phases: hearing / orchestration / plan / spec / code / doc / review (keep only completed ones)
- Outcome: shipped / blocked / retry
- Tests: <list tests run and results>
- Artifacts: <files changed or key outputs>
- Risks/Follow-ups: <remaining risks or items for next cycle>
```
