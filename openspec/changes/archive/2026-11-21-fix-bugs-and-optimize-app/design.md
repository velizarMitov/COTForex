# Design

## Context

- The app is a Streamlit script (`app.py`) with three pages. Data comes from `cftc_api.py` (Socrata HTTP, about 1.2 s per market, measured live) and `mt5_api.py` (local MetaTrader5 terminal). `data_processor.py` merges them, `charts.py` draws them, and `ui_components.py` renders the metric tiles.
- Environment: Python venv on Windows, Streamlit 1.56, pandas 3.0, Plotly 6.6, numpy 2.4. There are no tests, and `pytest` is not installed.
- `cftc_api.py` and `mt5_api.py` do not import Streamlit, and `main.py` runs without Streamlit. That separation is worth keeping.
- Requirements are in `specs/`. The motivation is in proposal.md.

## Goals / Non-Goals

**Goals:**
- Make every spec scenario checkable by an offline `pytest` run.
- Keep `cftc_api.py` and `mt5_api.py` free of Streamlit, so the CLI and tests import them without a Streamlit runtime.
- Keep each fix small and local. No restructuring beyond what the proposal lists.

**Non-Goals:**
- Changing COT↔MT5 date alignment, percentile math (beyond the min/max consistency fix), or chart visuals other than marker orientation.
- Adding type checking, linting or CI.

## Decisions

### D1. Cache in `data_processor.py`, not in the API modules
Add two private cached wrappers in `data_processor.py`:
- `_cot(name)` with `@st.cache_data(ttl="6h")`
- `_prices(symbol, num_bars)` with `@st.cache_data(ttl="15m")`

All data access goes through them: `load_and_align_data`, `get_comparison_data`, and so on.
- **Why the TTLs:** CFTC publishes weekly (Friday), so 6 h is plenty fresh. The current MT5 weekly bar moves intraday, so it gets a shorter TTL.
- **Why here:** the API modules stay Streamlit-free. `st.cache_data` also works outside a Streamlit runtime (it falls back to an in-memory cache with a warning), so `main.py` and the tests still work.
- **Alternatives:**
  - `functools.lru_cache`: rejected. It has no TTL, and it returns the same mutable object, which `load_and_align_data` then mutates.
  - Caching inside `cftc_api.py`: rejected, because it couples that module to Streamlit.

### D2. Do not cache failures: raise inside the cached function
`st.cache_data` caches whatever is returned, including an empty DataFrame, but it does not cache exceptions. So each cached wrapper raises a private `_EmptyResult` exception when the underlying fetch returns an empty frame. The public callers catch it and turn it into a failure reason.
- **Why:** this meets the "Failed fetch is not cached" scenario with no extra cache-invalidation logic.

### D3. `load_and_align_data` returns a `NamedTuple` with an `error` field
`AlignedData(merged, cot, dxy, mt5, error)`, where `error` is `None` on success or one of these messages:
- `"COT data for <pair> unavailable"`
- `"USD Index COT data unavailable"`
- `"MT5 price data for <symbol> unavailable (is the terminal running and logged in?)"`
- `"No overlapping dates between COT and MT5 data"`

A NamedTuple still unpacks positionally, so the change to the two call sites in `app.py` stays small. They show `st.error(result.error)`.
- **Alternative:** raising custom exceptions to the page. Rejected, because every page would need its own try/except.

### D4. Marker orientation keyed on `usd_is_base`
`build_comparison_chart` already computes `usd_is_base`. The marker spec table becomes conditional:

| Pair type | Crowded long | Crowded short |
|---|---|---|
| USD-quote | red ▼ above price | green ▲ below price |
| USD-base (`usd_is_base`) | green ▲ below price | red ▼ above price |

Labels name the futures side, for example "Crowded LONG Japanese Yen futures (52w pct ≥ 90)".
- **Alternative:** inverting the price series for USD-base pairs. This is the README's claimed "auto-inversion", which doesn't exist. Rejected: it changes every chart and is out of scope. The README will be corrected instead.

### D5. Crosshair owned by the caller
- Remove the unconditional `apply_shared_crosshair(fig)` from `build_stacked_chart`. `app._build_chart` already applies it when the toggle is on.
- `build_comparison_chart` keeps always-on crosshair, since it has no toggle.
- Drop the `try/except` in `apply_shared_crosshair`: `hoversubplots` exists in every Plotly version `requirements.txt` allows (≥5.21).

### D6. 52W Min/Max computed alongside the percentile
`calculate_extremes` also writes `52W Min` and `52W Max` columns, using the same `window` and `min_periods`. `get_comparison_data` reads the latest row through one `_extreme_row(label, df)` helper, which replaces the two copied branches. If a value is missing, the row gets `None`, not `int(nan)`, which would raise.

In `app.py`:
- Drop `fillna(0)`.
- Format the table with `Styler.format(na_rep="")`.
- The threshold filters already drop NaN rows (NaN comparisons are False).
- `to_csv` already writes NaN as empty.

### D7. Symbol map in `symbols.py`
`symbols.py` holds `COT_TO_MT5` and the derived `MT5_TO_COT`. `app.py`, `data_processor.py` and `main.py` import from there. This removes the reverse-dict that is rebuilt in two places, and stops the app from importing the legacy chart script.

### D8. `main.py` becomes a thin CLI
`python main.py [COT_NAME]` loads through `load_and_align_data`, builds `build_stacked_chart`, and calls `fig.show()`. The ~120 lines of duplicated legacy charting are deleted. The entry point stays, but it now renders the same chart as the app.

### D9. Shared sidebar helper in `app.py`
`_chart_sidebar(key_prefix)` returns `(pair, mode, date_density, crosshair, comparison_opts, num_bars)`. It is used by the Main (`"main"`) and Open Interest (`"oi"`) pages. Every widget gets a prefixed key. On first load, the Main page's widgets reset once because their keys change. That is acceptable.

### D10. Offline tests with `pytest`
`tests/` holds:
- **`test_cftc_api.py`**: alignment, percentile and momentum, using synthetic frames. `_fetch_rows` is monkeypatched to return unsorted rows and rows with bad dates.
- **`test_data_processor.py`**: failure reasons and no-caching-of-failures. The fetchers are monkeypatched, and `st.cache_data.clear()` runs in a fixture.
- **`test_charts.py`**: marker orientation and crosshair. Checked by inspecting `fig.data` (trace marker symbol and colour) and `fig.layout.hoversubplots`.
- **`test_extremes_report.py`**: row content and NaN handling.

`pytest` goes in a new `requirements-dev.txt` (`-r requirements.txt` + `pytest`). `mt5_api` imports `MetaTrader5` at module load. That package is installed in the venv, and tests never call it.

## Risks / Trade-offs

- **Stale data for up to 6 h after a Friday CFTC release.** The app runs with the default toolbar, so the user can clear the cache from Streamlit's top-right menu; this is noted in the README. A dedicated refresh button is out of scope.
- **The MT5 cache key includes `num_bars`**, so moving the slider fetches again once per distinct value. That is cheap (a local terminal call) and acceptable.
- **The marker flip changes signals that users of USD-base pairs have seen until now.** It fixes a real bug, so it is called out in the proposal's user-visible changes.
- **`st.cache_data` hashes arguments.** All arguments are small strings and ints, so the overhead is negligible.

## Migration Plan

No data migration is needed. Roll back with `git revert`. Install dev deps with `python -m pip install -r requirements-dev.txt`.
