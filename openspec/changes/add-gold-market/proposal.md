# Proposal

## Why

Gold is a core instrument next to the currency pairs, but the app only covers the CFTC TFF report (financial futures), where gold does not exist. Gold's positioning is in the CFTC Disaggregated Futures Only report (`GOLD`, COMEX, code 088691), with the same weekly history (2006-06-13 onward) and a Managed Money category that matches Leveraged Funds. The user's MT5 broker names the symbol `GOLD`, not `XAUUSD`, so symbol names also need resolving.

## What Changes

- Add gold as a selectable market on every page. Its COT data comes from the Disaggregated report (Managed Money), mapped to the same metrics as the currencies, so the 52-week percentile, historical zones, crowded signal, charts and Extremes report work unchanged.
- Resolve the MT5 symbol for gold from a list of common broker names (`XAUUSD`, `GOLD`, and suffixed variants), so it works whatever the broker calls it.
- Show prices with a sensible number of decimals per instrument (gold 2, JPY pairs 3, others 5). Today every price uses 5.
- Tell the user, wherever gold is shown, that its positioning category (Managed Money) is not identical to Leveraged Funds, so levels are not directly comparable with the currencies.

**Out of scope:** Micro Gold, other commodities, a gold-specific USD correlation view, and changing the USD Index panel (it stays TFF).

## Capabilities

### New Capabilities
_None._

### Modified Capabilities
- `market-data-pipeline`: adds requirements for the gold data source and for MT5 symbol resolution.
- `positioning-charts`: adds requirements for per-instrument price precision and the gold category notice.

## Impact

- **Code:** `cftc_api.py` (second data source), `symbols.py`, `mt5_api.py`, `charts.py`, `ui_components.py`, `app.py`, tests, README.
- **Dependencies:** none. **Users:** a new "XAUUSD" entry in the pair lists; other pairs' decimals change (JPY shows 3).
