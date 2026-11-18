# Specification Analysis Report

Output of `/speckit-analyze` (2026-11-18), run after `/speckit-tasks`. The command is read-only;
this file is a verbatim copy of its report, saved so that the analysis is part of the history.
Inputs: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`,
`.specify/memory/constitution.md` (v1.0.0).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | spec.md:L184 (FR-012), research.md:L29 (R2) | FR-012 says "try earlier dates one by one", research R2 steps back by *business* days (weekends skipped). Implementations following the spec literally would request Saturday/Sunday too. | Reword FR-012 to "earlier business days one by one (weekends skipped)". |
| U1 | Underspecification | LOW | spec.md:L196 (FR-016), tasks.md:L85 (T027) | The loading indicator required by FR-016 and Constitution I is in contracts/ui.md but no task names it explicitly. | Add "spinner on Convert, skeleton while rates load" to T027. |
| I2 | Inconsistency | LOW | tasks.md:L140 (T042), plan.md:L85-130 | `run.bat` is created by T042 but absent from the plan's source tree. | Add `run.bat` to the plan structure. |
| T1 | Terminology | LOW | spec.md:L211, data-model.md (Notice) | Spec lists notice types "weekend, not published, offline"; data model uses `WEEKEND`, `NOT_PUBLISHED`, `NOT_YET_PUBLISHED`, `SAVED_COPY`. "Offline" is an error state, not a notice. | Align the spec entity description with the data model. |
| D1 | Duplication | LOW | tasks.md:L80 (T022), tasks.md:L130 (T039) | T022 creates the full page incl. the date field (needed by FR-005 in US1); T039 again "creates" the date field. | Make T039 about min/max limits, the «Сегодня» chip and notice banners only. |
| C1 | Coverage | LOW | spec.md:L222 (SC-001), tasks.md:L114 (T034) | The "repeat ≤ 0.5 s" part of SC-001 relies on `MemoizingRateProvider`, delivered in US3. The US1 MVP alone may not meet it. | Accept: documented; BNM normally answers in 0.2–0.5 s anyway. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 amount field | Yes | T022, T027 | |
| FR-002 currency selectors + search | Yes | T025, T027 | |
| FR-003 date field & range | Yes | T007, T022, T039 | see D1 |
| FR-004 swap + auto recalculation | Yes | T027, T039 | |
| FR-005 Convert disabled / Enter | Yes | T027 | |
| FR-006 result + both rates | Yes | T017, T020, T027 | |
| FR-007 rate date + source | Yes | T020, T035 | |
| FR-008 input rules | Yes | T007, T029–T031 | |
| FR-009 same currency | Yes | T017 | |
| FR-010 symmetry | Yes | T017, T047 | |
| FR-011 weekends | Yes | T006, T037 | |
| FR-012 not published fallback | Yes | T037, T038 | see I1 |
| FR-013 offline offer, saved mode, empty state | Yes | T033, T035, T036 | |
| FR-014 saved copy survives restart | Yes | T032, T033, T050 | |
| FR-015 malformed = unavailable | Yes | T015, T033 | |
| FR-016 responsive + loading indicator | Partial | T023, T027 | see U1 |
| FR-017 light/dark, ≥ 360 px | Yes | T023, T026 | |
| FR-018 Russian texts | Yes | T020, T029, T038 | |
| FR-019 rounding | Yes | T011, T051 | |
| FR-020 local web GUI, local assets | Yes | T012, T028 | |

**Constitution Alignment Issues:** none. Principle II (SOLID) is reflected in T008 (ports), T013
(single composition root) and the adapter tasks; Principle VI in Phase 8; Principle VII in T002.

**Unmapped Tasks:** T042 (`run.bat`) — convenience, see I2.

**Metrics:**

- Total Requirements: 20 functional + 6 success criteria
- Total Tasks: 53
- Coverage %: 100 % of FRs have ≥ 1 task (FR-016 partially explicit)
- Ambiguity Count: 0
- Duplication Count: 1
- Critical Issues Count: 0

**Next Actions**: no CRITICAL issues — implementation may start. Recommended before
`/speckit-implement`: apply the small remediations for I1, U1, I2, T1, D1 (manual edits of spec.md,
plan.md, tasks.md).

**Remediation**: approved by the student's general instruction to work autonomously; applied in the
next commit (`docs(spec): fix inconsistencies reported by analyze`).
