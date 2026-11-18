---

description: "Task list for the currency converter implementation"
---

# Tasks: Currency Converter with Official Moldovan Rates

**Input**: Design documents from `/specs/001-currency-converter/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Unit tests are required by the lab and by Constitution Principle VI. They are collected
in the final phase (Phase 8) because they are developed on a separate git branch (`test/unit-tests`).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Paths are relative to the repository root; the package is `currency_converter/`

## Git mapping

| Phases | Branch |
|--------|--------|
| 1–7 | `feature/implementation` (one commit per task group) |
| 8 | `test/unit-tests` |
| Lab report | `docs/report` |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create the package skeleton per plan.md: `currency_converter/{domain,application,adapters,presentation,web}/__init__.py`, `currency_converter/__init__.py` (`__version__ = "1.0.0"`), `currency_converter/__main__.py`, `main.py` launcher, `currency_converter/web/static/{css,js,img}/`
- [X] T002 [P] Create `pyproject.toml` (project metadata, `requires-python >= 3.10`, `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["."]`) and `requirements-dev.txt` (`pytest>=8`)
- [X] T003 [P] Implement `AppConfig` and `parse_config(argv, environ)` in `currency_converter/config.py`: `--host` (127.0.0.1), `--port` (8765), `--data-dir` / `CURRENCY_CONVERTER_DATA_DIR` (default per research R6), `--source-url` (BNM base URL), `--timeout` (8 s), `--no-browser`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain model, ports and the HTTP shell that every story needs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement the error hierarchy from data-model.md in `currency_converter/domain/errors.py` (`ConverterError`, `FieldError`, `ValidationError`, `CurrencyNotAvailableError`, `RateSourceError` and subclasses, `NoSavedCopyError`)
- [ ] T005 [P] Implement `Currency`, `ExchangeRate`, `RateTable`, `MDL` in `currency_converter/domain/models.py` (frozen dataclasses, `per_unit`, `currencies()`, `find()`)
- [ ] T006 [P] Implement `is_weekend()` and `previous_business_day()` in `currency_converter/domain/calendar.py`
- [ ] T007 [P] Implement `AmountParser`, `RateDateParser` and `ConversionRequestValidator` (all FR-008 rules, collects every field error) in `currency_converter/domain/validation.py`
- [ ] T008 Define the ports `HttpClient`, `RateTableParser`, `RateProvider`, `RateCache`, `Clock`, `BrowserLauncher` as `typing.Protocol` in `currency_converter/ports.py`
- [ ] T009 [P] Implement `SourceKind`, `NoticeKind`, `Notice`, `SavedCopy`, `SavedCopyInfo`, `RateLookup`, `RatesUnavailableError` in `currency_converter/application/lookup.py`
- [ ] T010 [P] Implement `SystemClock` in `currency_converter/adapters/clock.py`
- [ ] T011 [P] Implement display formatting (`format_amount`, `format_rate`, `format_date`, `format_datetime`; research R5) in `currency_converter/presentation/formatting.py`
- [ ] T012 Implement the HTTP shell in `currency_converter/web/server.py`: request handler factory with injected controller, routing `GET /`, `GET /static/*` (traversal-safe, explicit MIME map), `GET/POST /api/*`, JSON responses, 16 KiB body limit, security headers, catch-all 500 with logging
- [ ] T013 Implement the composition root `build_application(config)` and `main()` in `currency_converter/bootstrap.py`: UTF-8 console (research R9), logging, port selection (research R10), start server, print URL, Ctrl+C shutdown

**Checkpoint**: `python main.py --no-browser` starts and serves an empty page

---

## Phase 3: User Story 1 - Convert at today's official rate (Priority: P1) 🎯 MVP

**Goal**: amount + two currencies + Convert → result, rates in both directions, rate date and source; swap

**Independent Test**: quickstart V1–V5

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `UrllibHttpClient` (timeout, User-Agent, maps `URLError`/timeouts/HTTP ≥ 400 to `SourceUnavailableError`) in `currency_converter/adapters/http_client.py`
- [ ] T015 [P] [US1] Implement `BnmXmlParser` (empty body → `NoRatesPublishedError`, broken XML / missing fields → `MalformedResponseError`, `Decimal` values, nominal) in `currency_converter/adapters/bnm.py`
- [ ] T016 [US1] Implement `BnmRateProvider` (URL `…?get_xml=1&date=DD.MM.YYYY`, uses `HttpClient` + `RateTableParser`) in `currency_converter/adapters/bnm.py`
- [ ] T017 [P] [US1] Implement `CurrencyConverter` and `Conversion` (cross rate through MDL, inverse rate, same currency) in `currency_converter/domain/conversion.py`
- [ ] T018 [US1] Implement `RateService.lookup(requested_date)` live path in `currency_converter/application/rate_service.py`
- [ ] T019 [US1] Implement `ConverterService.rates()` / `convert()` (validate → lookup → convert) in `currency_converter/application/converter_service.py`
- [ ] T020 [P] [US1] Implement source labels in `currency_converter/presentation/messages_ru.py` and `present_lookup`, `present_currencies`, `present_conversion` in `currency_converter/presentation/json_presenter.py` (contracts/http-api.md)
- [ ] T021 [US1] Implement `ApiController` (`/api/health`, `/api/rates`, `/api/convert`) in `currency_converter/web/api.py` and wire it in `bootstrap.py`
- [ ] T022 [US1] Create the page structure per contracts/ui.md in `currency_converter/web/static/index.html` and the logo/favicon in `currency_converter/web/static/img/logo.svg`
- [ ] T023 [P] [US1] Create the design system and components (tokens, light/dark, glass card, pickers, swap, button, result card, chips, banners, skeletons, motion, reduced motion, ≥ 360 px) in `currency_converter/web/static/css/styles.css`
- [ ] T024 [P] [US1] Implement the fetch wrapper `ApiClient` in `currency_converter/web/static/js/api.js`
- [ ] T025 [P] [US1] Implement the searchable `CurrencyPicker` component (popular first, keyboard navigation) in `currency_converter/web/static/js/currency-picker.js`
- [ ] T026 [P] [US1] Implement the theme switch in `currency_converter/web/static/js/theme.js`
- [ ] T027 [US1] Implement the page controller in `currency_converter/web/static/js/app.js`: load rates, enable/disable Convert, Enter key, convert, swap with auto-recalculation, result card, copy result, latest-request-wins, loading indicators (spinner on Convert, skeleton while rates load; FR-016)
- [ ] T028 [P] [US1] Implement `AppWindowLauncher`, `DefaultBrowserLauncher`, `FallbackBrowserLauncher` in `currency_converter/adapters/browser.py` and use them in `bootstrap.py` (skipped with `--no-browser`)

**Checkpoint**: US1 works end to end online

---

## Phase 4: User Story 2 - Clear feedback on invalid input (Priority: P2)

**Goal**: every invalid value produces a precise message at the field and no conversion

**Independent Test**: quickstart V6–V7

- [ ] T029 [US2] Add Russian texts for every `FieldError` code and for `CurrencyNotAvailableError` in `currency_converter/presentation/messages_ru.py`
- [ ] T030 [US2] Map `ValidationError` → 422 `VALIDATION` with `fields[]` and `CurrencyNotAvailableError` → 422 in `currency_converter/web/api.py` / `json_presenter.py`
- [ ] T031 [US2] Show field errors (outline, message, shake), clear them on edit and hide a stale result in `currency_converter/web/static/js/app.js` and `styles.css`

**Checkpoint**: US1 + US2 work

---

## Phase 5: User Story 3 - Keep working without internet (Priority: P2)

**Goal**: no crash offline, offer of the saved copy with its dates, saved copy survives restarts

**Independent Test**: quickstart V10–V12

- [ ] T032 [P] [US3] Implement `JsonFileRateCache` (schema 1, atomic write via temp + `os.replace`, corrupted/missing → `None`) in `currency_converter/adapters/json_cache.py`
- [ ] T033 [US3] Extend `RateService`: save the saved copy after each live success, raise `RatesUnavailableError(cause, saved_info)` on source failures, `lookup(..., use_saved=True)` mode with `SAVED_COPY` notice, `NoSavedCopyError` in `currency_converter/application/rate_service.py`
- [ ] T034 [P] [US3] Implement `MemoizingRateProvider` (positive results only, 30 min TTL, thread-safe) in `currency_converter/adapters/memo.py` and wire it in `bootstrap.py`
- [ ] T035 [US3] Present `SOURCE_UNAVAILABLE` (503, `saved` info), `NO_SAVED_COPY` (404) and saved source labels in `json_presenter.py`, `messages_ru.py`, `web/api.py`
- [ ] T036 [US3] Implement banners/toasts in `currency_converter/web/static/js/notices.js` and the offline flow in `app.js`: offer banner, saved-copy mode banner with «Попробовать онлайн», empty state with «Повторить» on start

**Checkpoint**: US1–US3 work; app survives network loss and restarts

---

## Phase 6: User Story 4 - Rate for a chosen date, weekends and holidays (Priority: P3)

**Goal**: explicit fallback for weekends, unpublished dates and tomorrow

**Independent Test**: quickstart V8–V9

- [ ] T037 [US4] Implement the weekend shift and the not-published fallback (≤ 10 days back, `RatesNotFoundError`) with `WEEKEND` / `NOT_PUBLISHED` / `NOT_YET_PUBLISHED` notices in `currency_converter/application/rate_service.py`
- [ ] T038 [US4] Add notice texts and `RATES_NOT_FOUND` mapping in `messages_ru.py`, `json_presenter.py`, `web/api.py`
- [ ] T039 [US4] Date limits (min 2000-01-01, max tomorrow), «Сегодня» chip, info banners for notices and auto-recalculation on date change in `index.html` / `app.js` (the field itself comes from T022)

**Checkpoint**: all user stories work independently

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T040 [P] Write `README.md` (purpose, requirements, run, options, data directory, architecture overview)
- [ ] T041 [P] Write the operating manual `docs/USER_GUIDE.md` (Russian, every screen state and scenario, troubleshooting)
- [ ] T042 [P] Add Windows launcher `run.bat`
- [ ] T043 Run quickstart.md scenarios V1–V12 and fix findings

---

## Phase 8: Unit tests (branch `test/unit-tests`)

**Purpose**: Constitution Principle VI; required coverage: parsing, conversion incl. reverse direction, empty/malformed source responses, input validation

- [ ] T044 [P] Record fixtures in `tests/fixtures/`: business day and weekend BNM answers, empty body, document without `<Valute>`, malformed XML, missing `<Value>`, non-numeric value
- [ ] T045 [P] Parser tests in `tests/unit/test_bnm_parser.py`
- [ ] T046 [P] Provider and HTTP error mapping tests (fake `HttpClient`) in `tests/unit/test_bnm_provider.py`
- [ ] T047 [P] Conversion tests (direct, reverse, cross, nominal 10/100, same currency, symmetry) in `tests/unit/test_conversion.py`
- [ ] T048 [P] Validation tests (all FR-008 cases) in `tests/unit/test_validation.py`
- [ ] T049 [P] Rate service tests (weekend, fallback, window exhausted, offline with/without saved copy, saved mode, cache refresh) in `tests/unit/test_rate_service.py`
- [ ] T050 [P] Cache tests (round trip, survives a new instance = restart, corrupted/missing/foreign schema) in `tests/unit/test_json_cache.py`
- [ ] T051 [P] Formatting/presenter tests in `tests/unit/test_presentation.py`
- [ ] T052 [P] API controller tests (200/422/503/404 payloads) in `tests/unit/test_api.py`
- [ ] T053 Add the test section to `README.md`; run `python -m pytest` — all green

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → user stories
- **US1 (Phase 3)** is the MVP and provides the API/UI shell used by later stories
- **US2, US3, US4** depend on US1's API and UI files (same files, so done sequentially in priority
  order: US2 → US3 → US4)
- **Polish (Phase 7)** after all stories; **Unit tests (Phase 8)** last, on its own branch

### Within Each User Story

- Domain/adapters before services, services before API, API before UI

### Parallel Opportunities

- T002/T003; T004–T007, T009–T011; T014/T015/T017/T020; T023–T026/T028; T032/T034; T040–T042;
  all of T044–T052

---

## Parallel Example: User Story 1

```text
Task: "T014 UrllibHttpClient in currency_converter/adapters/http_client.py"
Task: "T015 BnmXmlParser in currency_converter/adapters/bnm.py"
Task: "T017 CurrencyConverter in currency_converter/domain/conversion.py"
Task: "T023 styles.css" / "T024 api.js" / "T025 currency-picker.js" / "T026 theme.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1–2 → foundation
2. Phase 3 (US1) → **validate V1–V5** → usable converter

### Incremental Delivery

US2 (validation feedback) → US3 (offline + saved copy) → US4 (dates & fallback) → polish → tests.

---

## Notes

- Commit after each task group with bilingual (EN/RU) Conventional Commit messages
- Mark tasks `[X]` here when done
- Every deviation from plan/spec found during implementation is recorded in `docs/agent-log.md`
