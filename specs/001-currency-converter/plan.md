# Implementation Plan: Currency Converter with Official Moldovan Rates

**Branch**: `spec/currency-converter` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-currency-converter/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A local web application: a Python standard-library HTTP server runs on `127.0.0.1`, serves a
single-page interface (HTML/CSS/vanilla JS modules, no CDN) and a small JSON API. Rates come from the
National Bank of Moldova XML feed (Russian locale endpoint). The core is a layered, SOLID design:
pure domain (models, Decimal conversion, validation, business calendar) → application services
(rate lookup with weekend / not-published fallback, offline handling, saved copy) → adapters (HTTP,
BNM XML parser, JSON file cache, clock, browser launcher) → delivery (HTTP API + static UI). One
composition root wires everything with constructor injection. See [research.md](research.md) for the
decisions and [contracts/](contracts/) for the API and UI contracts.

## Technical Context

**Language/Version**: Python 3.10+ (developed and verified on CPython 3.12, Windows 11)

**Primary Dependencies**: standard library only — `http.server` (`ThreadingHTTPServer`),
`urllib.request`, `xml.etree.ElementTree`, `decimal`, `json`, `dataclasses`, `typing.Protocol`,
`webbrowser`/`subprocess` (browser window). Front end: HTML5, CSS (custom properties, grid,
`backdrop-filter`), vanilla ES modules.

**Storage**: one JSON file with the last successful response in the user data directory
(`%APPDATA%\CurrencyConverter\rates-cache.json`; `~/.local/share/currency-converter/` elsewhere),
written atomically; overridable with `--data-dir` / `CURRENCY_CONVERTER_DATA_DIR`. UI preferences
(theme, last pair) in browser `localStorage` (convenience only).

**Testing**: pytest (dev dependency only), network-free: recorded BNM XML fixtures + fakes for
every port. One command: `python -m pytest`.

**Target Platform**: Windows 10/11 desktop (primary), Linux/macOS; any modern Chromium/Firefox
browser. Edge/Chrome "app window" mode when available.

**Project Type**: local web application (desktop-style GUI served on localhost).

**Performance Goals**: first conversion ≤ 3 s on a normal connection (BNM answers in ~0.2–0.5 s);
repeated conversions for the same date ≤ 0.5 s thanks to an in-memory memo.

**Constraints**: offline-capable; HTTP timeout 8 s (offline message ≤ 12 s, SC-003); bind to
`127.0.0.1` only; no runtime third-party packages; UI usable from 360 px width.

**Scale/Scope**: single user, ~40 currencies, one window, ~15 Python modules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Pre-design | Post-design |
|-----------|------|------------|-------------|
| I. GUI first | Browser-window GUI, responsive, light/dark, non-blocking fetch with spinner | PASS | PASS — see [contracts/ui.md](contracts/ui.md) |
| II. SOLID | Ports as `Protocol`s, adapters replaceable, single composition root, domain without I/O | PASS | PASS — layer map below; `bootstrap.py` is the only place that instantiates adapters |
| III. Never crash | Typed errors → JSON error payloads → banners; catch-all at HTTP boundary | PASS | PASS — error table in [contracts/http-api.md](contracts/http-api.md) |
| IV. Offline & provenance | Saved copy survives restart; explicit opt-in; notices for weekend/fallback/saved | PASS | PASS — `RateLookup.source`, `notices` in data model |
| V. Decimal money | `Decimal` end-to-end; strings in JSON; ROUND_HALF_UP for display only | PASS | PASS |
| VI. Testability | Network-free unit tests, fixtures, fakes; separate final phase/branch | PASS | PASS |
| VII. Minimal deps | stdlib runtime; local assets; pytest only for dev | PASS | PASS |

No violations → Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-currency-converter/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── http-api.md
│   └── ui.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
main.py                              # launcher: python main.py [--port --data-dir --no-browser ...]
currency_converter/
├── __init__.py                      # __version__
├── __main__.py                      # python -m currency_converter
├── config.py                        # AppConfig + CLI/env parsing
├── bootstrap.py                     # composition root (the only place that knows concrete classes)
├── domain/                          # pure: no I/O, no UI, no HTTP
│   ├── models.py                    # Currency, ExchangeRate, RateTable, MDL
│   ├── errors.py                    # typed error hierarchy
│   ├── calendar.py                  # weekend / previous business day
│   ├── conversion.py                # CurrencyConverter, Conversion
│   └── validation.py                # AmountParser, RateDateParser, ConversionRequestValidator
├── ports.py                         # Protocols: HttpClient, RateTableParser, RateProvider,
│                                    #            RateCache, Clock, BrowserLauncher
├── application/
│   ├── lookup.py                    # RateLookup, Notice, SourceKind, SavedCopy
│   ├── rate_service.py              # RateService: fallback, offline, saved-copy mode
│   └── converter_service.py         # ConverterService: use-case facade for the delivery layer
├── adapters/
│   ├── http_client.py               # UrllibHttpClient
│   ├── bnm.py                       # BnmXmlParser, BnmRateProvider
│   ├── memo.py                      # MemoizingRateProvider (decorator, positive results, TTL)
│   ├── json_cache.py                # JsonFileRateCache (atomic write, corruption-tolerant)
│   ├── clock.py                     # SystemClock
│   └── browser.py                   # AppWindowLauncher, DefaultBrowserLauncher, FallbackLauncher
├── presentation/
│   ├── formatting.py                # Decimal → "1 234,56", dates → "03.11.2026"
│   ├── messages_ru.py               # Russian texts for error codes and notices
│   └── json_presenter.py            # domain/app objects → JSON-ready dicts
└── web/
    ├── api.py                       # ApiController: query/body → service → presenter → (status, dict)
    ├── server.py                    # HTTP handler (routing, static files, security headers)
    └── static/
        ├── index.html
        ├── css/styles.css
        ├── js/app.js                # page controller
        ├── js/api.js                # fetch wrapper
        ├── js/currency-picker.js    # searchable picker component
        ├── js/notices.js            # banners & toasts
        ├── js/theme.js              # light/dark switch
        └── img/logo.svg
tests/
├── fixtures/                        # recorded BNM XML responses + broken variants
└── unit/                            # parser, conversion, validation, rate service, cache, presenter, api
pyproject.toml                       # pytest configuration
requirements-dev.txt                 # pytest
```

**Structure Decision**: single Python package with a layered layout (domain → application →
adapters/presentation → web). The front end is static and lives inside the package so it is served
locally and installed together with the code. Dependency direction is strictly inward: `web` and
`adapters` import `application`/`domain`/`ports`; `domain` imports nothing from the project except
itself.

### SOLID map

| Principle | Where it shows |
|-----------|----------------|
| SRP | Parser only parses XML; provider only builds URLs and calls the HTTP client; cache only persists; converter only calculates; validator only validates; presenter only formats; server only routes |
| OCP | New source = new `RateProvider` + `RateTableParser`; memoisation added as a decorator without editing `BnmRateProvider`; new browser strategy = new `BrowserLauncher` |
| LSP | `MemoizingRateProvider` and fakes are drop-in `RateProvider`s; any `RateCache` (JSON file, in-memory fake) works in `RateService` |
| ISP | Six tiny protocols; the server never sees the cache, the converter never sees HTTP |
| DIP | `RateService(provider, cache, clock)`, `ConverterService(rate_service, converter, validator, clock)` receive abstractions; `bootstrap.build_application()` is the only wiring point |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations.
