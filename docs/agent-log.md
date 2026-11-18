# Agent log / Журнал работы агентов

Every step performed by an AI agent is recorded here: which agent and model, which Spec Kit
command (skill) was followed, what came out and what had to be corrected.
Каждый шаг, выполненный ИИ-агентом, фиксируется здесь: какой агент и модель, какая команда
Spec Kit выполнялась, что получилось и что пришлось исправлять.

Agent / Агент: **Claude Code (desktop app), model Claude Opus 5.5** — for every step below.
Spec Kit skills were executed by reading `.github/skills/speckit-*/SKILL.md` and following
them step by step (Claude Code reads the same skill files that Copilot uses).

| # | Date | Stage | Spec Kit command / action | Result | Problems & manual intervention |
|---|------|-------|---------------------------|--------|--------------------------------|
| 1 | 2026-11-04 | init | `specify init --here --integration copilot --script ps` (run by the student in a terminal) | `.specify/`, `.github/skills/` | First attempt (`specify init .`) produced no files in Lab3; `uv` had been installed into another user profile — re-run by the student. |
| 2 | 2026-11-18 | constitution | `/speckit-constitution` | constitution v1.0.0, 7 principles | — |
| 3 | 2026-11-18 | specify | `/speckit-specify` | `specs/001-currency-converter/spec.md` (4 user stories, 19 FR, 6 SC) + `checklists/requirements.md` | Checklist passed on the first pass. Branch was created manually (`spec/currency-converter`): the git extension of Spec Kit is not installed, so the skill only creates the directory. |
| 4 | 2026-11-18 | clarify | `/speckit-clarify` | 5 Q/A in `## Clarifications`, FR-004/012/013 refined, FR-020 added | The student delegated all decisions to the agent ("делай всё самостоятельно"), so the agent answered its own questions. Main decision: local web GUI (browser window) instead of tkinter — chosen for UI quality. |
| 5 | 2026-11-18 | plan | `/speckit-plan` (`setup-plan.ps1 -Json` → template copied) | `plan.md`, `research.md`, `data-model.md`, `contracts/http-api.md`, `contracts/ui.md`, `quickstart.md` | Research included live requests to bnm.md: weekend answers carry Friday values under the requested date, future dates return an empty body, some nominals are 10/100. Printing Cyrillic in the cp1252 Windows console crashed the research script → recorded as decision R9. |
