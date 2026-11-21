# Design

## Context

`cftc_api.py` hardcodes the TFF dataset (`gpe5-46if`), `contract_market_name` filter and `lev_money_*` fields. Everything downstream (metrics, zones, signal, charts) uses the canonical columns built from those. Gold's live data (verified): dataset `72hh-3qpy`, `cftc_contract_market_code = '088691'`, fields `m_money_positions_long_all`, `m_money_positions_short_all`, `pct_of_oi_m_money_long_all`, `pct_of_oi_m_money_short_all`; 1,067 rows, no nulls or duplicates. MT5 on this broker names gold `GOLD`.

## Goals / Non-Goals

**Goals:** gold flows through the existing pipeline with minimal new code; broker-independent symbol.
**Non-Goals:** a general multi-report framework, other commodities, or changing signal math.

## Decisions

### D1. A per-market source table in `cftc_api.py`
`_SOURCES` maps a canonical market name to `(dataset, where-clause, field names)`; all existing markets use the TFF entry, `GOLD` uses the Disaggregated entry. `_fetch_rows` renames the gold fields to the canonical `lev_money_*` names right after the request, so `fetch_cftc_data`, `calculate_*` and every consumer stay untouched. **Alternative:** a second `fetch_*` function with its own metrics; rejected because it would duplicate the signal pipeline. Filtering gold by contract code (not name) avoids matching Micro Gold or Coinbase gold.

### D2. Canonical symbol is `XAUUSD`; the broker name is resolved at fetch time
`symbols.py` maps `GOLD -> XAUUSD`, so the UI shows a stable name. `mt5_api.resolve_symbol(name)` tries `SYMBOL_ALIASES[name]` (`XAUUSD`, `GOLD`, `XAUUSD.m`, `XAUUSD.`, `GOLD.`) against `mt5.symbol_info`, and falls back to a wildcard search `*XAU*`. **Alternative:** a config file for the broker name; rejected as extra setup for something detectable.

### D3. Precision from the symbol
`symbols.price_decimals(symbol)`: 2 for `XAUUSD`, 3 for symbols ending in `JPY`, else 5. Charts build hover formats from it (`f".{d}f"`); metrics use it directly. **Alternative:** infer from price magnitude; rejected because the rule is clearer per symbol.

### D4. Category notice
A `st.caption` under the sidebar pair selector (shared `_chart_sidebar`) when `pair == "XAUUSD"`.

## Risks / Trade-offs

- **Managed Money vs Leveraged Funds are different populations:** levels are not comparable; mitigated by the notice. The percentile and zones are self-relative, so signals remain internally consistent.
- **Wildcard symbol fallback could pick a wrong instrument (for example XAUEUR):** only used when named aliases fail, and it prefers names containing `XAUUSD`; otherwise it reports unavailable.
- **JPY decimals change from 5 to 3:** intended.
