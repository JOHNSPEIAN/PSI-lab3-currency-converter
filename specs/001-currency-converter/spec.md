# Feature Specification: Currency Converter with Official Moldovan Rates

**Feature Branch**: `spec/currency-converter`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Currency converter with a graphical interface. Data source: official
exchange rates of the National Bank of Moldova (XML published per date). Interface: amount input,
source currency, target currency, convert button disabled until the required fields are filled,
result, rate date and data source. Mandatory behaviour: no network — no crash, clear message, offer
the last successfully received rate with its date; weekends and holidays — handle an empty response
and use the last available rate, telling the user; invalid input (negative, zero, letters, empty) —
error, no conversion; identical currencies — no error; caching — the last successful response is
stored locally and survives a restart. Conversion must be correct in both directions. The interface
must be beautiful and pleasant to use."

## Clarifications

### Session 2026-11-18

- Q: What form does the graphical interface take — a native desktop window or a local web page? → A: A local web application: the program runs on the user's computer and opens its interface in a browser window (app-style window when the browser supports it). It needs no internet for its own assets.
- Q: What do the currency selectors show when the app starts offline? → A: The currencies of the saved copy (with the offline offer shown); if there is no saved copy, an empty state with a "Retry" action is shown instead of the form.
- Q: After the user accepts the saved rates, is the offer repeated for every conversion? → A: No. The app stays in "saved copy" mode for the session, with a visible banner and a "Try live data" action; a successful live download leaves that mode.
- Q: Should changes after a result is shown recalculate automatically? → A: Swap, currency change and date change recalculate automatically when a result is already shown; amount edits are applied with Convert or Enter.
- Q: How is the "tomorrow" date handled before BNM publishes it? → A: Like any unpublished date (FR-012): the latest earlier rate is used with an explanation that the rate for tomorrow is usually published after 13:00 Chisinau time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert an amount at today's official rate (Priority: P1)

A user opens the application, types an amount, picks the currency they have and the currency they
want, presses "Convert" and immediately sees the converted amount, the exchange rate in both
directions, the date of the rate and where the rate comes from. A single "swap" action reverses the
direction and recalculates.

**Why this priority**: this is the reason the product exists; everything else protects this flow.

**Independent Test**: with network access, convert 100 USD to MDL and compare with the official rate
published on bnm.md for the same date; swap and convert back.

**Acceptance Scenarios**:

1. **Given** the app is open and rates for today are available, **When** the user enters `100`,
   selects USD → MDL and presses Convert, **Then** the result equals 100 × the official USD rate,
   and the rate date and source "National Bank of Moldova" are shown.
2. **Given** a result USD → MDL is shown, **When** the user presses Swap, **Then** the direction
   becomes MDL → USD and the result is recalculated with the inverse rate.
3. **Given** two foreign currencies (EUR → USD), **When** the user converts, **Then** the cross rate
   through MDL is used and both "1 EUR = x USD" and "1 USD = y EUR" are shown.
4. **Given** the same currency is selected on both sides, **When** the user converts, **Then** no
   error appears, the result equals the amount and the rate is 1.
5. **Given** the amount field is empty, **When** the window is shown, **Then** the Convert button
   is disabled; it becomes enabled as soon as the amount, both currencies and the date are filled.

---

### User Story 2 - Clear feedback on invalid input (Priority: P2)

A user makes a typo — a negative number, zero, letters, an empty field or an impossible date — and
the application explains exactly what is wrong next to the field without performing a conversion.

**Why this priority**: wrong input must never produce a wrong number; this is an acceptance item.

**Independent Test**: enter each invalid value from the list in the acceptance scenarios and confirm
that an error is shown and no result is produced.

**Acceptance Scenarios**:

1. **Given** the amount `-5`, **When** the user converts, **Then** the message "amount must be
   greater than zero" is shown at the amount field and no result is displayed.
2. **Given** the amount `0`, `abc`, `12a`, `1,2,3` or only spaces, **When** the user converts,
   **Then** a specific error is shown and no conversion is performed.
3. **Given** the amount `1 000,50` or `1000.50`, **When** the user converts, **Then** it is accepted
   as one thousand and fifty hundredths.
4. **Given** a date later than tomorrow or a malformed date, **When** the user converts, **Then**
   an error is shown at the date field and no conversion is performed.
5. **Given** a previous result is shown, **When** an invalid conversion is attempted, **Then** the
   old result is hidden so that it cannot be mistaken for the answer to the new input.

---

### User Story 3 - Keep working without internet (Priority: P2)

The user is offline (or the source does not answer). The application does not crash: it explains
that the source is unreachable and, if rates were downloaded earlier, offers to continue with the
last successfully received rates, clearly stating their rate date and when they were saved. This
also works after the application has been closed and reopened.

**Why this priority**: explicit acceptance criteria ("network off does not crash the app", "cached
rate survives a restart").

**Independent Test**: convert once online, close the app, disconnect the network, reopen the app
and convert — the cached rate is offered with its date and used after confirmation.

**Acceptance Scenarios**:

1. **Given** no network and no saved rates, **When** the app starts or the user converts, **Then**
   the app stays open and shows "no connection to the National Bank of Moldova, no saved rates yet,
   check the connection and retry", with a retry action.
2. **Given** no network and saved rates from an earlier session, **When** the user converts,
   **Then** the app shows the offline message and offers "use saved rates of DD.MM.YYYY (saved
   DD.MM.YYYY HH:MM)".
3. **Given** the user accepted the saved rates, **When** the conversion is shown, **Then** the
   source reads "saved copy (offline)" together with the rate date, never "National Bank of Moldova
   (live)".
4. **Given** the source returns a malformed answer, **When** the user converts, **Then** it is
   treated like an unavailable source (message + offer of saved rates).
5. **Given** the network comes back, **When** the user retries, **Then** live rates are used again
   and the saved copy is refreshed.

---

### User Story 4 - Rate for a chosen date, weekends and holidays (Priority: P3)

The user picks a past date (or tomorrow). If the official rate was not published for that date — a
weekend, a holiday or a date whose rate is not out yet — the application uses the last available
earlier rate and tells the user which date was used instead and why.

**Why this priority**: required behaviour, but most conversions use today's rate.

**Independent Test**: choose a Saturday, a Sunday, a public holiday and tomorrow before 13:00
Chisinau time; each time the used date and an explanation are shown.

**Acceptance Scenarios**:

1. **Given** the user selects a Saturday or Sunday, **When** they convert, **Then** the rate of the
   last preceding business day is used and the message says "no official rate is published on
   weekends; the rate of <date> is used".
2. **Given** the source returns no rates for the selected date, **When** the user converts, **Then**
   the application steps back to the closest earlier date with rates and says "rate for <requested
   date> is not published; the rate of <used date> is used".
3. **Given** no rates are found within 10 days before the requested date, **When** the user
   converts, **Then** an error message explains that no rates were found and no result is shown.
4. **Given** the selected date has a published rate, **When** the user converts, **Then** no
   fallback message is shown and the displayed rate date equals the requested date.

---

### Edge Cases

- Source answers with an empty body, with a document without currencies, or with broken markup.
- Source answers slowly: the window stays responsive and shows progress; a request gives up after
  a bounded time and is then handled as "unreachable".
- Saved rates file is missing, empty or corrupted: treated as "no saved rates", the app still starts.
- A currency is quoted per several units (nominal ≠ 1, e.g. per 10 or 100 units): rates are
  normalised per one unit.
- Very small results (e.g. 1 MDL → a currency with a high unit value) are shown with enough digits
  to be non-zero; very large amounts are rejected above a documented maximum.
- The selected currency is missing in the rate list of the fallback date: an error is shown for that
  currency instead of a wrong result.
- The user changes inputs while a request is running: only the latest request updates the screen.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a field for the amount to convert.
- **FR-002**: The system MUST provide source and target currency selectors listing MDL plus every
  currency published by the source for the active date, each shown with its code and name, and
  allow searching the list by code or name.
- **FR-003**: The system MUST provide a rate date field, pre-filled with today's date, accepting
  dates from 01.01.2000 up to tomorrow.
- **FR-004**: The system MUST provide a swap action that exchanges source and target currencies.
  When a result is already shown, swap, currency change and date change MUST recalculate it
  automatically; amount edits are applied with Convert or Enter.
- **FR-005**: The Convert action MUST be disabled until the amount, both currencies and the date are
  filled; pressing Enter in the amount field MUST trigger the conversion when it is enabled.
- **FR-006**: The system MUST display the converted amount and the exchange rate in both directions
  (1 A = x B and 1 B = y A).
- **FR-007**: The system MUST display the date of the rate actually used and the data source:
  "National Bank of Moldova" for live data or "saved copy" with the save time for cached data.
- **FR-008**: The system MUST reject, with a message at the related field and without converting:
  empty amount, non-numeric text, zero, negative values, more than 4 decimal places, values above
  1 000 000 000 000, malformed dates and dates outside the allowed range. Both "." and "," are
  accepted as decimal separators; spaces between digit groups are ignored.
- **FR-009**: When source and target currencies are identical, the system MUST return the amount
  unchanged with rate 1 and no error.
- **FR-010**: Conversion MUST be symmetric: converting the result back with the swapped currencies
  MUST return the original amount within display rounding (0.01).
- **FR-011**: For a Saturday or Sunday the system MUST use the rate of the last preceding business
  day and explicitly tell the user which date is used.
- **FR-012**: When the source publishes no rates for a date (empty answer or no currencies), the
  system MUST try earlier dates one by one (up to 10 days back), use the first date with rates and
  explicitly tell the user both dates; if nothing is found it MUST show an error. For tomorrow's
  date the message MUST add that the rate is usually published after 13:00 Chisinau time.
- **FR-013**: When the source is unreachable (no network, timeout, server error) the system MUST
  NOT crash, MUST show an understandable message and, if saved rates exist, MUST offer to use them,
  stating their rate date and save time. Using them requires an explicit user action; after it the
  app stays in "saved copy" mode for the session with a visible banner and a "Try live data" action.
  When the app starts offline without a saved copy, an empty state with "Retry" replaces the form.
- **FR-014**: The system MUST store the last successful source response locally; the stored copy
  MUST survive application restarts and MUST be refreshed after each successful download.
- **FR-015**: A malformed source response MUST be handled like an unreachable source (FR-013).
- **FR-016**: The interface MUST stay responsive during downloads and show a loading indicator.
- **FR-017**: The interface MUST offer light and dark appearance (following the system setting by
  default, switchable by the user) and MUST remain usable at narrow window widths (≥ 360 px).
- **FR-018**: All user-visible texts MUST be in Russian.
- **FR-019**: Rounding for display: converted amounts to 2 decimal places (more significant digits
  when the absolute value is below 0.01), rates to 4 decimal places; rounding half up.
- **FR-020**: The interface MUST run locally on the user's computer and open in a browser window;
  all its assets MUST be served locally so the interface itself loads without internet.

### Key Entities

- **Currency**: ISO code (e.g. USD), human-readable name; MDL is the base currency.
- **Exchange Rate**: currency, nominal (number of units quoted), value in MDL for the nominal;
  derived rate per one unit.
- **Rate Table**: all exchange rates published for one date; knows its date.
- **Rate Lookup Result**: rate table + requested date + date actually used + source kind
  (live/saved) + save time + list of notices for the user (weekend, not published, offline).
- **Conversion Result**: amount, source and target currency, converted amount, direct and inverse
  rate, provenance (rate date, source).
- **Saved Copy**: the last successful source response with the date it is valid for and the moment
  it was saved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With a normal connection a conversion result appears within 3 seconds after pressing
  Convert; repeated conversions for the same date appear within 0.5 seconds.
- **SC-002**: 100 % of the invalid inputs listed in User Story 2 are rejected with a message and
  produce no result.
- **SC-003**: With the network disabled the application never closes or freezes; the offline
  message appears within 12 seconds of pressing Convert.
- **SC-004**: For any supported currency pair, converting X from A to B and the result back from B
  to A returns X within 0.01.
- **SC-005**: After a restart without network, saved rates are offered on the first conversion
  attempt in 100 % of cases where at least one successful download happened before.
- **SC-006**: On every result screen a user can name the rate date and the data source without any
  additional action.

## Assumptions

- Users are individuals converting amounts for information; no transactions are executed.
- The official BNM rate is the rate "in force" for a date; commercial bank rates are out of scope.
- BNM may answer a weekend date with the previous business day's values labelled with the
  requested date; the application treats weekends explicitly instead of relying on that behaviour.
- Public holidays cannot be detected without a calendar; they are handled by the "no rates
  published" rule (FR-012) when the source returns nothing for them.
- "Today" is the date of the user's computer.
- Only the most recent successful response is guaranteed to be stored; storing more dates is an
  optimisation.
- Accounts, history across devices, charts and notifications are out of scope for this version.
