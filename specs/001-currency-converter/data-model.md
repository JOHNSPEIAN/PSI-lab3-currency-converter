# Data Model: Currency Converter

All monetary values are `decimal.Decimal`. All entities are immutable (`@dataclass(frozen=True)`).

## Domain

### Currency
| Field | Type | Rules |
|-------|------|-------|
| code | str | ISO 4217, 3 upper-case letters |
| name | str | human-readable (Russian from BNM) |

`MDL = Currency("MDL", "Молдавский лей")` — base currency, always available.

### ExchangeRate
| Field | Type | Rules |
|-------|------|-------|
| currency | Currency | |
| nominal | int | > 0 (1, 10, 100) |
| value | Decimal | > 0, MDL for `nominal` units |

Derived: `per_unit = value / nominal`.

### RateTable
| Field | Type | Rules |
|-------|------|-------|
| rate_date | date | date the rates are valid for |
| rates | tuple[ExchangeRate, ...] | unique codes, non-empty, MDL not included |

Operations: `currencies()` → MDL + all codes sorted; `per_unit(code)` → Decimal (MDL → 1);
raises `CurrencyNotAvailableError` for an unknown code.

### Conversion
| Field | Type |
|-------|------|
| amount | Decimal |
| source, target | Currency |
| result | Decimal (unrounded) |
| rate | Decimal — 1 source = rate target |
| inverse_rate | Decimal — 1 target = inverse_rate source |

Invariant: `source == target` ⇒ `rate == inverse_rate == 1`, `result == amount`.

### Validated request
`ConversionRequest(amount: Decimal, source: str, target: str, rate_date: date)` — produced only by
`ConversionRequestValidator`; invalid input yields `ValidationError(errors=[FieldError...])`.

`FieldError(field: "amount"|"source"|"target"|"date", code: str, params: dict)`; codes:
`AMOUNT_EMPTY, AMOUNT_NOT_A_NUMBER, AMOUNT_ZERO, AMOUNT_NEGATIVE, AMOUNT_TOO_MANY_DECIMALS,
AMOUNT_TOO_LARGE, CURRENCY_EMPTY, CURRENCY_INVALID, DATE_EMPTY, DATE_INVALID, DATE_TOO_EARLY,
DATE_IN_FUTURE`.

## Errors (domain/errors.py)

```text
ConverterError
├── ValidationError(errors: list[FieldError])
├── CurrencyNotAvailableError(code, rate_date)
└── RateSourceError
    ├── SourceUnavailableError(reason)        # network, timeout, HTTP >= 400
    ├── MalformedResponseError(reason)        # broken XML / missing fields
    ├── NoRatesPublishedError(rate_date)      # empty body / no <Valute>
    ├── RatesNotFoundError(requested, earliest_tried)   # fallback window exhausted
    └── NoSavedCopyError                      # saved mode requested, nothing saved
```

Application layer adds `RatesUnavailableError(ConverterError)` — see "Offline outcome" below.

## Application

### SourceKind
`LIVE` (downloaded now or memoised) | `SAVED` (local saved copy).

### Notice
| Field | Type | Meaning |
|-------|------|---------|
| kind | `WEEKEND` \| `NOT_PUBLISHED` \| `NOT_YET_PUBLISHED` \| `SAVED_COPY` | |
| requested_date | date | |
| used_date | date | |
| saved_at | datetime \| None | only for SAVED_COPY |

### SavedCopy
| Field | Type |
|-------|------|
| table | RateTable |
| saved_at | datetime (local, second precision) |
| source_id | str (`"bnm"`) |

### RateLookup
| Field | Type |
|-------|------|
| table | RateTable |
| requested_date | date |
| used_date | date (`== table.rate_date`) |
| source | SourceKind |
| saved_at | datetime \| None |
| notices | tuple[Notice, ...] |

### Offline outcome
`RatesUnavailableError(cause: RateSourceError, saved: SavedCopyInfo | None)` where
`SavedCopyInfo(rate_date, saved_at)` lets the UI offer the saved copy (FR-013).

## State transitions (UI session mode)

```text
           start / retry ok
   ┌────────────── LIVE ◄──────────────┐
   │                │ source fails     │ "Try live data" succeeds
   │                ▼                  │
   │        OFFLINE_OFFER ── accept ──► SAVED
   │                │ no saved copy
   │                ▼
   └──────────── EMPTY (retry) ────────┘
```

## Persistence: `rates-cache.json`

```json
{
  "schema": 1,
  "source_id": "bnm",
  "saved_at": "2026-11-18T12:30:05",
  "rate_date": "2026-11-18",
  "rates": [
    {"code": "EUR", "name": "Евро", "nominal": 1, "value": "20.1538"},
    {"code": "HUF", "name": "Венгерский Форинт", "nominal": 100, "value": "5.5244"}
  ]
}
```
Values are strings to keep Decimal precision. Unknown `schema` or invalid content → ignored.
