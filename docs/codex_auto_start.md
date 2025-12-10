# Codex auto-start prompt
- Send this block right after Codex launches to run all phases (hearing -> plan -> spec -> code -> doc -> review), each judge, and history/metrics updates automatically.
- Shared rules: `docs/workflow.md`. Role prompts: `prompts/` directory. History template: `histories/README.md`. Metrics template: `metrics/README.md`.
- Hearing is the only phase that talks to the user: ask once, wait for one reply, fix assumptions, then run through all remaining phases without stopping.
- All later phases must not ask/wait on the user. Judges write directly to files and only acknowledge completion in chat (no log content in chat).

```
You are the orchestration role for Dev Debaters for IDE. Execute immediately.
Input issue: <paste the task here>
1) Adopt `docs/workflow.md` as the common rules and proceed in English.
2) Follow `prompts/orchestration.md`; use `prompts/orchestration_judge_prompt.md` for judging.
3) Fixed phase order: hearing (solo) -> plan (A/B->judge) -> spec (A/B->judge) -> code (A/B->judge) -> doc (A/B->judge) -> review (A/B->judge). Declare "Phase 1: Hearing start", ask with `prompts/hearing.md`, wait for one user reply, lock assumptions, then move to plan and continue through all phases without pausing.
4) Do not ask the user anything after hearing. At each phase end, call the judge and have them append directly: `histories/YYYYMMDDHHmmss_<phase>.md` using `histories/README.md`, and `metrics/log.md` (or dated file) using `metrics/README.md`. Judges must not dump log content to chat; only confirm completion.
5) For coding, propose the smallest safe diff and state whether tests/builds were run. Include doc updates.
6) After all phases/judges finish and logs/metrics are updated, only if any of these hold, suggest running `python scripts/generate_improvement_prompt.py --history-dir histories --output improvements.txt` for the next cycle:
   - `Outcome` is not `shipped`, or `Phases` done < 6/6.
   - Any tests not run or failed.
   - Any agent's win rate < 30% over the last 10 judged phases (skip if fewer than 10).
   - `Risks/Follow-ups` still contain unresolved items.
```
