# Tasks

## 1. Signal computation (crowded-positioning-signal)

- [x] 1.1 In `cftc_api.py`, add `crowded_masks(...)` and `calculate_crowded(...)` (design D1, D2) and call it from `get_cot_data`; add the new columns to the empty-frame schema. Verify: new tests in `tests/test_cftc_api.py` cover warm-up (no zone before 156 weeks), no-look-ahead (appending data leaves earlier zones unchanged), and the three confluence scenarios (stretched only, rare only, both).
- [x] 1.2 In `data_processor.load_and_align_data`, carry `OI Zone Lo/Hi` for the pair and USD Index into the merged frame. Verify: a test in `tests/test_data_processor.py` checks that the merged frame has `OI Zone Lo/Hi` and `OI Zone Lo_dxy/Hi_dxy`.

## 2. Charts (crowded-positioning-signal)

- [x] 2.1 In `build_comparison_chart`, build markers from `crowded_masks` (slider on the percentile side only) and update marker help text. Verify: tests in `tests/test_charts.py` confirm no marker on a stretched-but-not-rare week, a marker on a confluence week, and that the orientation tests from `fix-bugs-and-optimize-app` still pass.
- [x] 2.2 Replace flat zone shapes with evolving Hi/Lo line traces, including the inverted USD Index swap/negate and the Spread panel (design D3). Verify: tests check that the Hi line trace is not constant for a drifting series, is absent during warm-up, and that the inverted panel's upper line equals the negated Lo.

## 3. Alerts and warnings (crowded-positioning-signal)

- [x] 3.1 Switch `ui_components` alerts to `Crowded Signal`, with an insufficient-history message during warm-up. Verify: tests with stub frames cover bullish, bearish, normal and warm-up verdicts; with the live data today, EURUSD shows no bearish alert.
- [x] 3.2 Add a `Crowded` column to the Extremes rows and make `crowded_assets` use it. Verify: updated tests in `tests/test_extremes_report.py` show a percentile-1 asset inside its zone raising no warning, and CSV export still matches the table.

## 4. Documentation and integration

- [x] 4.1 Update the sidebar help text and the README ("USD-aware markers" and a new short "What counts as crowded" paragraph). Verify: README states the confluence rule, the 156-week warm-up and that nothing fires before about 2009.
- [x] 4.2 Run `python -m pytest -q`, `openspec validate confluence-crowded-signal --strict`, and the headless smoke run with live CFTC data (stubbed MT5). Verify: all pass, marker counts per market are about 10-15 over 20 years, and no page raises an exception. Then check the live EURUSD view once MT5 is logged in.

## Workflow follow-up

- Archive `fix-bugs-and-optimize-app` first, then reconcile the overlapping requirements in `positioning-charts` and `sentiment-extremes-report` with MODIFIED deltas, then archive this change.
