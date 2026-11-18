# Research: Currency Converter

Phase 0 of `/speckit-plan`. Every decision below lists the alternatives that were rejected.
Source observations were made on 2026-11-04 and 2026-11-18 with real requests to bnm.md.

## R1. Data source

- **Decision**: National Bank of Moldova, XML feed
  `https://www.bnm.md/ru/official_exchange_rates?get_xml=1&date=DD.MM.YYYY` (Russian locale).
- **Rationale**: official rate for Moldova; free, no API key, no quotas; history by date; the
  Russian endpoint returns Russian currency names, matching the Russian UI (FR-018). The format is
  stable and simple: `<ValCurs Date="..."><Valute><CharCode/><Nominal/><Name/><Value/></Valute>...`.
- **Alternatives considered**: free JSON APIs (exchangerate.host, open.er-api.com, frankfurter.app)
  — need keys or have quotas, use ECB/commercial data instead of the official Moldovan rate, and do
  not quote MDL officially; scraping the HTML page of bnm.md — fragile compared with the XML feed.

## R2. Observed source behaviour (drives FR-011/FR-012)

| Request | Observed answer |
|---------|-----------------|
| Business day (03.11.2026, 18.11.2026) | 200, `ValCurs Date` = requested date, 40 `<Valute>` |
| Saturday 31.10.2026 / Sunday 01.11.2026 | 200, values identical to Friday 30.10, but `Date` = requested date |
| Holiday 01.01.2026 | 200, 40 currencies |
| Tomorrow before publication (19.11.2026 at the time of the check) and future dates | **404 Not Found** with an empty body (0 bytes) — *corrected during implementation; first recorded as "200 with an empty body" because only the body size had been checked* |
| `Nominal` | 1 for most currencies; 10 for ALL, AMD, …; 100 for HUF, … |

- **Decision**: (a) weekend dates are shifted to the previous Friday *before* requesting, so the
  displayed rate date is the real publication date; (b) HTTP 404, an empty body or a document without
  `<Valute>` means "not published" → step back one business day, up to 10 calendar days from the
  requested date; (c) the date label returned by BNM is trusted for business days.
- **Alternatives considered**: trusting BNM's weekend answer as-is — would show "rate of Sunday",
  which is misleading and hides the fallback the lab requires to be explicit.

## R3. GUI technology

- **Decision**: local web app — stdlib `ThreadingHTTPServer` on `127.0.0.1` + single page with
  vanilla ES modules; opened in an Edge/Chrome `--app` window when available, otherwise in the
  default browser.
- **Rationale**: the lab allows desktop *or* web; CSS gives a far better-looking, responsive UI with
  light/dark themes and animations than tkinter/ttk; no runtime dependencies; the HTTP boundary
  makes the presentation layer naturally separated (SRP/DIP) and testable without a GUI.
- **Alternatives considered**: tkinter/ttk — zero deps but dated look, hard to make responsive and
  themed; PySide6/Qt — beautiful but ~200 MB dependency; Flask/FastAPI — third-party dependency for
  what three routes need; Electron/Tauri — another language stack.

## R4. Non-blocking fetch

- **Decision**: the browser calls the API with `fetch` (async), shows a spinner and ignores stale
  responses using a request counter; the server is threaded, so a slow BNM call never blocks the UI.
- **Alternatives considered**: worker thread + polling — unnecessary with async fetch.

## R5. Money arithmetic and formatting

- **Decision**: `Decimal` everywhere; per-unit rate = `Value / Nominal`; cross rate
  `rate(A→B) = perUnit(A) / perUnit(B)`, MDL per unit = 1; inverse = `1 / rate`. Amounts are rounded
  to 2 decimals for display (ROUND_HALF_UP); if `|x| < 0.01` and `x ≠ 0`, 2 significant digits are
  shown; rates to 4 decimals. Decimals travel through JSON as strings. Display uses Russian grouping
  (`1 234,56`, narrow no-break space) produced on the server, so the browser never does float math.
- **Alternatives considered**: `float` — rounding artefacts; formatting in JS with
  `Intl.NumberFormat` — would require parsing decimals into floats.

## R6. Saved copy (cache)

- **Decision**: `JsonFileRateCache` keeps exactly the last successful response (rate table + rate
  date + saved-at timestamp + source id), schema-versioned, written to a temp file and moved with
  `os.replace` (atomic). Missing/corrupted/foreign-schema files → "no saved copy" (never a crash).
  Additionally `MemoizingRateProvider` memoises positive answers in memory for 30 minutes.
- **Alternatives considered**: SQLite — overkill for one record; caching raw XML — couples the cache
  to one source (violates OCP); caching negative ("not published") answers — would hide a rate
  published later the same day.

## R7. Offline detection

- **Decision**: `URLError`, `socket.timeout`/`TimeoutError`, `ConnectionError`, HTTP status ≥ 400
  → `SourceUnavailableError`; malformed XML → `MalformedResponseError` (handled the same way,
  FR-015). Timeout 8 s.

## R8. Input formats

- **Decision**: amount regex accepts digits with optional sign, one `.` or `,` decimal separator and
  space/no-break-space thousands groups (`1 000,50`); max 4 decimals; max 1e12. Date accepts ISO
  `YYYY-MM-DD` (HTML date input) and `DD.MM.YYYY`; range 2000-01-01 … tomorrow.

## R9. Windows console encoding

- **Decision**: reconfigure `stdout`/`stderr` to UTF-8 with `errors="replace"` at start-up.
- **Rationale**: observed during research — printing Russian currency names in a Windows console
  using cp1252 raised `UnicodeEncodeError`. Logging must never crash the app (Principle III).

## R10. Port and browser window

- **Decision**: default port 8765; if busy, the next free port up to 8784, then an OS-assigned port.
  Edge (`msedge.exe`) or Chrome is started with `--app=<url>` for a desktop-like window; fallback is
  `webbrowser.open`. `--no-browser` disables launching (tests, demos).
