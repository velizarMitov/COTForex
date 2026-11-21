# Tasks

## 1. Setup

- [x] 1.1 Create `requirements-dev.txt` (`-r requirements.txt` + `pytest`) and install it into `.venv`. Verify: `.venv/Scripts/python.exe -m pytest --version` succeeds.
- [x] 1.2 Create `tests/__init__.py` and `tests/conftest.py`. The conftest puts the repo root on `sys.path` and adds an autouse fixture that calls `st.cache_data.clear()`. Verify: `python -m pytest` runs and collects 0 tests without import errors.
- [x] 1.3 Create `symbols.py` with `COT_TO_MT5` and the derived `MT5_TO_COT`. Switch `app.py` and `data_processor.py` to import from it, and delete their local reverse-dicts. Verify: `grep -n "from main import" *.py` returns nothing, and `python -c "import app"` succeeds.

## 2. CFTC metrics correctness (market-data-pipeline)

- [x] 2.1 In `cftc_api.fetch_cftc_data`, remove the loop that reassigns `pct_of_oi_*` from the unsorted `df`. Verify: a new test in `tests/test_cftc_api.py` stubs `_fetch_rows` with unsorted rows and a bad date row, and checks that each row's `Net_Pct_of_OI` == long% − short%.
- [x] 2.2 In `calculate_extremes`, add `52W Min` / `52W Max` columns using the same `window`/`min_periods` as the percentile. Verify: tests check that early rows (<26) are 50, a flat window is 50, and latest Net Position == `52W Max` ⇒ percentile 100.

## 3. Cached, failure-aware data loading (market-data-pipeline)

- [x] 3.1 Add cached wrappers `_cot(name)` (ttl 6h) and `_prices(symbol, num_bars)` (ttl 15m) to `data_processor.py`. They raise `_EmptyResult` on empty frames, so failures are never cached. Route all data access through them. Verify: a `tests/test_data_processor.py` test monkeypatches `get_cot_data`, counts calls, and checks that 2 successful loads = 1 call each and 2 failed loads = 2 calls.
- [x] 3.2 Change `load_and_align_data` to return `AlignedData(merged, cot, dxy, mt5, error)` with the four error messages from design D3. Verify: one test per message (pair COT empty, USD COT empty, MT5 empty, no overlap within 6 days), plus a success case with `error is None`.
- [x] 3.3 Update both `app.py` call sites to show `st.error(result.error)`. Verify: with the MT5 terminal closed, `streamlit run app.py` shows the MT5-specific message on the Main and Open Interest pages.

## 4. Chart fixes (positioning-charts)

- [x] 4.1 In `build_comparison_chart`, orient markers by `usd_is_base` per design D4, and relabel them as "Crowded LONG/SHORT <currency> futures (52w pct …)". Verify: tests in `tests/test_charts.py` build EURUSD and USDJPY figures from a synthetic frame with a forced extreme. They check that the marker trace symbol/colour and its y offset (above vs below price) match the spec scenarios.
- [x] 4.2 Remove the unconditional `apply_shared_crosshair` call from `build_stacked_chart`, and drop the `try/except` in `apply_shared_crosshair`. Verify: a test checks that `build_stacked_chart(...).layout.hoversubplots` is unset, and is `"axis"` after `apply_shared_crosshair`. Then manually toggle the crosshair on the Stacked view and confirm it switches on and off.

## 5. Extremes report (sentiment-extremes-report)

- [x] 5.1 Replace the two copied branches in `get_comparison_data` with one `_extreme_row(label, df)` helper that reads `52W Min`/`52W Max` from task 2.2 and gives `None` for missing values. Verify: tests in `tests/test_extremes_report.py` check that pair and USD rows have identical columns, and that a NaN percentile yields `None`.
- [x] 5.2 In `app.render_extremes_comparison`, remove `fillna(0)` and format the table with `na_rep=""`. Verify: a test checks that a NaN-percentile row raises no crowded-short warning and that `to_csv` leaves that cell empty. Manually confirm that the table, warnings and CSV render on the Extremes page.

## 6. Code cleanup

- [x] 6.1 Add `_chart_sidebar(key_prefix)` to `app.py`, and use it from the Main (`"main"`) and Open Interest (`"oi"`) pages. Verify: both pages render all sidebar controls, and switching pages raises no `DuplicateWidgetID` error.
- [x] 6.2 Replace `use_container_width=True` with `width="stretch"` in `st.plotly_chart` and `st.dataframe`. Verify: `grep -n use_container_width *.py` returns nothing, and the Streamlit console shows no deprecation warning.
- [x] 6.3 Rewrite `main.py` as a thin CLI (`python main.py [COT_NAME]`) using `load_and_align_data` + `build_stacked_chart` + `fig.show()`, and delete `plot_cot_with_dxy`. Verify: `python main.py "EURO FX"` opens the stacked chart in a browser with the MT5 terminal running.

## 7. Documentation

- [x] 7.1 Update `README.md`:
  - Features: remove the "Auto-Inversion" claim, describe filled-area panels and the Comparison/Stacked/Overlay/Heatmap views, and note caching and "Clear cache" from the Streamlit menu.
  - Project Structure: list every module, including `symbols.py`, `data_processor.py`, `charts.py`, `ui_components.py` and `tests/`, and add `requirements-dev.txt` plus the `pytest` command.
  - Leave the "Data Selection Rationale" section untouched.

  Verify: every file the README names exists, and the documented commands run.

## 8. Integration check

- [ ] 8.1 Run the full suite and a live smoke test. Verify:
  - `python -m pytest -q` passes.
  - With MT5 running, `streamlit run app.py` loads all three pages and all four chart views for EURUSD and USDJPY.
  - Toggling options after the first load triggers no new CFTC fetch (no repeated spinner delay).
  - `openspec validate fix-bugs-and-optimize-app` passes.

## Workflow follow-up

- After review, archive the change with the `openspec-archive-change` skill so the three capability specs move into `openspec/specs/`.
