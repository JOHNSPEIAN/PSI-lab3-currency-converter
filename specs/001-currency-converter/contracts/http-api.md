# Contract: local HTTP API

Base URL: `http://127.0.0.1:<port>`. JSON UTF-8. Decimals are strings. Dates are ISO `YYYY-MM-DD`
in fields named `*_date`; human-readable variants come in `*_display` fields (Russian formatting).
All user-visible `message` texts are Russian.

## GET /api/health

`200 {"status": "ok", "version": "1.0.0"}`

## GET /api/rates?date=YYYY-MM-DD&mode=live|saved

Loads the rate table for the date (default: today, `mode=live`).

`200`:
```json
{
  "status": "ok",
  "lookup": {
    "requested_date": "2026-11-15",
    "used_date": "2026-11-13",
    "used_date_display": "13.11.2026",
    "source": "live",
    "source_label": "Национальный банк Молдовы",
    "saved_at": null,
    "saved_at_display": null,
    "notices": [{"kind": "weekend", "level": "info", "message": "15.11.2026 — выходной день: ..."}]
  },
  "currencies": [
    {"code": "MDL", "name": "Молдавский лей", "nominal": 1, "rate_display": "1,0000"},
    {"code": "EUR", "name": "Евро", "nominal": 1, "rate_display": "20,1538"}
  ]
}
```

## POST /api/convert

Request: `{"amount": "1 000,50", "source": "USD", "target": "MDL", "date": "2026-11-18", "mode": "live"}`

`200`:
```json
{
  "status": "ok",
  "conversion": {
    "amount": "1000.50", "amount_display": "1 000,50",
    "source": {"code": "USD", "name": "Доллар США"},
    "target": {"code": "MDL", "name": "Молдавский лей"},
    "result": "18347.47", "result_display": "18 347,47",
    "rate": "18.3383", "rate_display": "18,3383",
    "inverse_rate": "0.0545", "inverse_rate_display": "0,0545"
  },
  "lookup": { "...": "same as /api/rates" }
}
```

## Error payloads

Every error: `{"status": "error", "error": {"code": "...", "message": "...", ...}}`

| HTTP | code | Extra fields | When |
|------|------|--------------|------|
| 422 | `VALIDATION` | `fields: [{"field","code","message"}]` | invalid amount / currency / date (no conversion done) |
| 422 | `CURRENCY_NOT_AVAILABLE` | `currency` | code not in the table of the used date |
| 503 | `SOURCE_UNAVAILABLE` | `saved: {"rate_date","rate_date_display","saved_at","saved_at_display"} \| null` | network/timeout/HTTP error or malformed response |
| 404 | `RATES_NOT_FOUND` | — | nothing published in the 10-day window |
| 404 | `NO_SAVED_COPY` | — | `mode=saved` but no saved copy |
| 400 | `BAD_REQUEST` | — | malformed JSON / body too large (> 16 KiB) |
| 404 | `NOT_FOUND` | — | unknown route |
| 500 | `INTERNAL` | — | unexpected exception (logged, never a stack trace) |

## Static files

`GET /` → `index.html`; `GET /static/<path>` → files under `web/static` only (path traversal
rejected with 404). Headers: explicit MIME types (`.js` → `text/javascript`), `Cache-Control:
no-store` for API, `Content-Security-Policy: default-src 'self'`, `X-Content-Type-Options: nosniff`.
