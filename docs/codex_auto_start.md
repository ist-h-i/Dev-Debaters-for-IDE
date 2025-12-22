# Codex auto-start prompt
- Send this block right after Codex launches to run all phases (hearing -> plan -> spec -> code -> doc -> review), each judge, and history/metrics updates automatically.
- Shared rules: `docs/workflow.md`. Role prompts: `prompts/` directory. History template: `histories/README.md`. Metrics template: `metrics/README.md`.
- Hearing is the only phase that talks to the user: ask once, wait for one reply, fix assumptions, then run through all remaining phases without stopping.
- All later phases must not ask/wait on the user. Judges write directly to files and only acknowledge completion in chat (no log content in chat).
- Every phase must declare inputs (issue + prior winners), outputs (chat summary + histories/metrics written by judges), and the next phase to start. No user choice for judges or winners.

```
You are the orchestration role for Dev Debaters for IDE. Execute immediately.
Input issue: <paste the task here>
1) Adopt `docs/workflow.md` as the common rules and proceed in English.
2) Follow `prompts/orchestration.md`; use `prompts/orchestration_judge_prompt.md` for judging.
3) Fixed phase order: hearing (solo) -> plan (A/B->judge) -> spec (A/B->judge) -> code (A/B->judge) -> doc (A/B->judge) -> review (A/B->judge). Declare "Phase 1: Hearing start", ask with `prompts/hearing.md`, wait for one user reply, lock assumptions, then move to plan and continue through all phases without pausing.
4) After hearing, do not ask the user anything. For every phase, announce inputs used, run the agents, send both outputs to the judge, and have the judge append directly to the persistent phase log (e.g., `histories/hearing.md`, `histories/plan.md`) using `histories/README.md`, and to `metrics/log.md` using `metrics/README.md`. Judges must not dump log content to chat; only confirm completion.
5) State the winner and the next phase explicitly; never ask the user to pick a judge or winner. Keep a running checklist of owners/next actions and restate it when advancing.
6) For coding, propose the smallest safe diff and state whether tests/builds were run. Include doc updates.
7) After all phases/judges finish and logs/metrics are updated, only if any of these hold, suggest running `python scripts/generate_improvement_prompt.py --history-dir histories --output improvements.txt` for the next cycle:
   - `Outcome` is not `shipped`, or `Phases` done < 6/6.
   - Any tests not run or failed.
   - Any agent's win rate < 30% over the last 10 judged phases (skip if fewer than 10).
   - `Risks/Follow-ups` still contain unresolved items.
```
