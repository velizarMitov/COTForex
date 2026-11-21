# Proposal

## Why

A full review of the COT vs MT5 Streamlit app found several bugs that show wrong information, plus a big performance problem. Streamlit reruns the whole script on every widget click, and nothing is cached. So every toggle refetches CFTC data (about 1.2 s per market, measured live) and reconnects to MT5. The Extremes page refetches 8 datasets on every click. Some bugs show traders misleading signals (for example, reversal markers pointing the wrong way on USD-base pairs). They should be fixed before more features are added on top.

## What Changes

**Bug fixes**
- Extreme-positioning markers on the price panel point the wrong way for USD-base pairs (USDJPY, USDCHF, USDCAD). Crowded-long JPY futures implies USDJPY *up*, but the app draws a red down-triangle above price. Markers will be oriented by the expected move of the *displayed pair*.
- The "Enable vertical crosshair" toggle on the Stacked view does nothing, because `build_stacked_chart` always applies the crosshair. The toggle will now control it.
- `fetch_cftc_data` overwrites the `pct_of_oi_*` columns with values from the unsorted, un-reset source frame. Rows can then end up misaligned whenever any row is dropped or reordered. The columns will stay aligned with their rows.
- The Extremes table runs `fillna(0)` before its threshold checks. A missing percentile therefore turns into a false "Extreme Bearish" warning. Missing values will be shown as missing and excluded from warnings.
- The Extremes table reports 52W Min/Max with `min_periods=1`, but the percentile uses `min_periods=26`. The two now use one consistent window.
- When loading fails, the app shows one generic error. It will now say which source failed (CFTC pair, CFTC USD Index, MT5) or that the dates don't overlap.

**Optimizations**
- Cache CFTC and MT5 fetches with `st.cache_data` and a TTL, so widget changes stop triggering network or terminal calls.
- Remove duplicated code:
  - one shared sidebar-controls helper for the Main and Open Interest pages
  - one helper for the Extremes table rows (pair and USD branches are copies today)
- Move the `COT_TO_MT5` symbol map out of `main.py` into its own module. `app.py` and `data_processor.py` will stop importing the legacy plotting script.
- Replace the old chart code in `main.py` with a thin CLI that reuses the shared pipeline and `build_stacked_chart`.
- Replace deprecated `use_container_width=True` with `width="stretch"` (Streamlit 1.56 warns on every render).

**Quality**
- Add a `pytest` suite for the pure data functions and the bug fixes above. It needs no network or MT5; fetchers are stubbed.
- Correct the README's stale facts: Features (no auto-inversion exists today; charts are filled areas, not bars) and Project Structure (missing modules, wrong `main.py` description).

**Out of scope**
- The README "Data Selection Rationale" section (S&P 500, Treasury yields, CPI) does not describe this app, but it was added on purpose in a recent commit, so it is left unchanged.
- New indicators, new pages, ML features, parallel or batched CFTC requests.
- Changing how COT dates map to MT5 weekly bars (`merge_asof` nearest, 6-day tolerance). The current behavior is kept.

## Capabilities

### New Capabilities
- `market-data-pipeline`: Fetching CFTC TFF and MT5 weekly data, deriving positioning metrics (net position, Net % of OI, week-over-week change, 52-week percentile), aligning them by date, caching, and reporting which source failed.
- `positioning-charts`: Plotly chart behavior for the Comparison, Stacked, Overlay and Heatmap views, including extreme-marker orientation and the crosshair toggle.
- `sentiment-extremes-report`: The multi-asset Extremes & Comparison table, its crowded-trade warnings, and CSV export.

### Modified Capabilities
_None. No specs exist yet._

## Impact

- **Code:** `cftc_api.py`, `mt5_api.py`, `data_processor.py`, `charts.py`, `app.py`, `ui_components.py`, `main.py`. New: `symbols.py`, `tests/`.
- **Dependencies:** add `pytest` as a dev dependency (new `requirements-dev.txt`). No runtime dependency changes.
- **Behavior visible to users:**
  - markers flip on USDJPY, USDCHF and USDCAD
  - the crosshair toggle now works
  - error messages are more specific
  - widget interactions are much faster after the first load
  - data refreshes at most once per cache TTL. The "Clear cache" option in Streamlit's menu forces a refresh.
- **No breaking changes** to function signatures used across modules, except `load_and_align_data`, which gains a failure-reason return value (internal only).
