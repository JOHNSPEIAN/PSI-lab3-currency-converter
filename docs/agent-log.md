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
