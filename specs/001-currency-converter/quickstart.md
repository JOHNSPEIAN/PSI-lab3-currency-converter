# Quickstart & validation scenarios

## Prerequisites

- Python 3.10+ (`python --version`)
- A Chromium-based browser (Edge/Chrome) or Firefox
- Internet access for the live scenarios

## Run

```powershell
python main.py                 # opens the app window
python main.py --no-browser    # only prints the URL
python main.py --data-dir .\tmp-data --port 8800
```

## Unit tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Manual validation (maps to spec acceptance scenarios)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| V1 | US1 direct | 100, USD → MDL, today, Convert | 100 × BNM USD rate; date + «НБМ» chip |
| V2 | US1 reverse | press ⇄ | MDL → USD recalculated automatically; converting the result back returns 100 |
| V3 | US1 cross | 100 EUR → USD | rate = EUR/USD via MDL; both directions shown |
| V4 | US1 same | USD → USD | result = amount, rate 1, no error |
| V5 | US1 button | clear amount | Convert disabled |
| V6 | US2 | `-5`, `0`, `abc`, `12a`, `1,2,3`, spaces | error under amount, no result |
| V7 | US2 | `1 000,50` | accepted |
| V8 | US4 weekend | pick a Saturday | blue banner: rate of the previous Friday is used |
| V9 | US4 not published | pick tomorrow before 13:00 Chisinau | banner: tomorrow's rate not yet published, today's used |
| V10 | US3 offline + saved | convert once online → close → `python main.py --source-url http://127.0.0.1:9/` (or disable Wi-Fi) → convert | amber banner with saved date; accept → amber source chip |
| V11 | US3 offline, nothing saved | `python main.py --data-dir .\empty --source-url http://127.0.0.1:9/` | empty state with «Повторить», no crash |
| V12 | US3 restart | V10 after a restart | saved copy still offered |

The `--source-url` option points the BNM adapter to an unreachable address — a reproducible way to
simulate "no network" without touching the system network settings.
