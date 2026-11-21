# Tasks

## 1. Gold COT data (market-data-pipeline)

- [x] 1.1 Add the per-market source table to `cftc_api.py` (design D1), accept `GOLD`/`XAUUSD` names, and rename gold fields to the canonical ones. Verify: tests stub `urlopen` and check the gold request uses dataset `72hh-3qpy`, code `088691` and Managed Money fields, that rows are renamed, and that Net Position is long minus short.
- [x] 1.2 Add `GOLD -> XAUUSD` in `symbols.py` and `price_decimals`. Verify: tests for the mapping and for decimals (gold 2, JPY 3, EURUSD 5).

## 2. MT5 symbol resolution (market-data-pipeline)

- [x] 2.1 Add `resolve_symbol` with aliases and the guarded wildcard fallback to `mt5_api.py`, and use it in `fetch_forex_data` (design D2). Verify: tests with a stubbed terminal cover GOLD-only, exact XAUUSD, and no match.

## 3. Display (positioning-charts)

- [x] 3.1 Use `price_decimals` in chart hover formats, heatmap price text, the momentum tile and the OI snapshot tile. Verify: tests check the hover template of an XAUUSD chart uses 2 decimals and a USDJPY chart 3, and the tile text for both.
- [x] 3.2 Add the Managed Money notice for gold in `_chart_sidebar` (design D4). Verify: a Streamlit `AppTest` shows the caption for XAUUSD and none for EURUSD.

## 4. Documentation and integration

- [x] 4.1 Update the README (gold support, Managed Money note, broker symbol resolution). Verify: README states the report, category and symbol behavior.
- [x] 4.2 Run `pytest`, `openspec validate add-gold-market --strict`, and the live check with real CFTC and MT5 data for XAUUSD on all pages and views. Verify: no exceptions, gold shows about 10-15 crowded markers, and the Extremes table has an XAUUSD row.
