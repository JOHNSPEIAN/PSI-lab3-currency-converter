# Currency Converter Constitution

## Core Principles

### I. Graphical Interface First

The product is used through a graphical interface only. A console application is not acceptable.

- Every user-facing capability (input, selection, conversion, status, errors, offline choice) MUST be
  reachable and visible in the GUI.
- The GUI MUST be a single, focused window/page that works at desktop and narrow (phone-sized) widths.
- Visual quality is a requirement, not decoration: consistent spacing scale, readable typography,
  light and dark themes, visible focus states, and motion that never hides information.
- The GUI MUST stay responsive while rates are being fetched (no frozen window, visible progress).

**Rationale**: the lab explicitly rejects console apps and grades the user experience.

### II. SOLID Architecture (NON-NEGOTIABLE)

- **SRP**: parsing, HTTP transport, caching, conversion math, input validation, orchestration and
  presentation live in separate modules/classes, each with one reason to change.
- **OCP**: a new rate source (another API or website) is added by writing a new adapter that
  implements an existing interface. The domain, application services and UI MUST NOT change.
- **LSP**: every implementation of an interface is substitutable; tests MUST be able to replace any
  adapter with a fake without special cases.
- **ISP**: interfaces are small and focused (`typing.Protocol`): rate provider, rate cache, HTTP
  client, clock. No "god" interface.
- **DIP**: the domain and application layers depend only on abstractions. Concrete classes are
  created and wired in exactly one composition root via constructor injection.
- The domain layer MUST NOT perform I/O and MUST NOT import UI, HTTP or file-system code.

**Rationale**: SOLID is an explicit acceptance requirement and keeps the source swappable.

### III. Resilience: Never Crash

- No network, timeouts, HTTP errors, empty or malformed source responses, corrupted cache files and
  invalid user input MUST NOT terminate the application.
- Every failure is converted into a typed error and then into a clear, human-readable message in the
  GUI that says what happened and what the user can do next.
- Unexpected exceptions at the boundary are logged and shown as a generic error, never as a stack
  trace.

**Rationale**: "network off does not crash the app" is an acceptance criterion.

### IV. Offline Capability and Honest Data Provenance

- The last successful source response MUST be persisted locally and survive application restarts.
- When the source is unreachable and cached data exists, the user MUST be offered the cached rates
  together with the rate date and the moment they were saved. Cached data is never presented as live.
- Whenever the rate used differs from the requested date (weekend, holiday, not yet published), the
  GUI MUST say so explicitly and name the date actually used.
- Every result shows the rate date and the data source.

**Rationale**: users make money decisions; they must know how fresh and where the numbers come from.

### V. Exact Money Arithmetic

- Rates and amounts MUST use decimal arithmetic (`decimal.Decimal`), never binary floating point.
- Rounding happens only for display, with an explicit, documented rounding mode (ROUND_HALF_UP).
- Conversion MUST be correct in both directions and for identical source/target currencies.

**Rationale**: float rounding errors are unacceptable in a currency converter.

### VI. Testability

- Business logic (parsing, conversion, fallback rules, validation, caching) is covered by unit tests.
- Unit tests MUST run locally with one command (`python -m pytest`) and MUST NOT access the network:
  recorded source fixtures and fakes are used instead.
- Unit tests are implemented in a dedicated final phase of `tasks.md` and on a dedicated git branch,
  as required by the lab (specs, implementation and tests live on separate branches).

**Rationale**: the lab requires unit tests on separate branches; fakes are possible thanks to DIP.

### VII. Minimal Dependencies

- Runtime: Python standard library only. Front-end assets (if any) are local files; no CDN, so the
  GUI also works offline.
- Development: `pytest` is the only additional dependency.

**Rationale**: the app must start on a clean university machine and work without internet access.

## Technology and Data Constraints

- Language: Python 3.10+ (developed on 3.12), Windows first, Linux/macOS supported.
- Primary data source: official exchange rates of the National Bank of Moldova (BNM), XML feed.
  Base currency MDL. The source adapter is replaceable (Principle II, OCP).
- Local data lives in the user profile directory, never next to the source code; the location is
  overridable for tests.
- All text visible to the user is in Russian; code, identifiers, comments and API fields are in
  English.

## Development Workflow and Quality Gates

- Spec-driven: constitution → specification → clarification → plan → tasks → analyze → implement.
  Specifications are committed before any implementation code (verifiable in git history).
- Git: one branch per stage (`spec/*`, `feature/*`, `test/*`, `docs/*`); `main` changes only through
  Pull Requests with merge commits (no squash), so the process remains visible.
- Commit messages follow Conventional Commits; the subject is in English, the body contains an
  English (`EN:`) and a Russian (`RU:`) description of the change.
- Small, meaningful commits: one logical step per commit; "everything done" commits are forbidden.
- Gate before merge: `python -m pytest` is green and the quickstart scenarios pass manually.

## Governance

- This constitution supersedes other practices of the project. Plans and tasks MUST include a
  Constitution Check; any violation MUST be justified in the plan's Complexity Tracking table.
- Amendments are made through a commit on a `spec/*` branch that updates this file, bumps the
  version and states the reason in the commit body.
- Versioning: MAJOR — principle removed or redefined; MINOR — principle or section added or
  materially expanded; PATCH — clarifications and wording.
- Every Pull Request review checks compliance with Principles I–VII.

**Version**: 1.0.0 | **Ratified**: 2026-11-18 | **Last Amended**: 2026-11-18
