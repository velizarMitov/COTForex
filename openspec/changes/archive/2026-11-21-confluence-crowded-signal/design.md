# Design

## Context

- Today three places each decide "extreme" separately: `charts.build_comparison_chart` (markers from the rolling percentile), `charts._add_extreme_zones` (flat P10/P90 over the full series), and the alert code in `ui_components.py` / `app.py` (rolling percentile >= 90 or <= 10).
- `cftc_api.get_cot_data` already produces `Net_Pct_of_OI` and `52-Week Percentile`. `data_processor.load_and_align_data` carries selected columns into the merged frame.
- Measured on live data (2006-2026): zones from full history versus expanding history agree on only about half the markers. The expanding zone needs 156 weeks, so the first zone is 2009-06-02.
- Motivation is in proposal.md; requirements are in the spec.

## Goals / Non-Goals

**Goals:** one definition of "crowded", computed once and reused by charts, alerts and warnings; no look-ahead.
**Non-Goals:** changing percentile math or marker density logic; back-testing the signal.

## Decisions

### D1. Compute zones and the signal in `cftc_api.py`
Add `calculate_crowded(df, threshold=90, min_periods=156)` called from `get_cot_data` after `calculate_extremes`. It adds columns:
- `OI Zone Lo` / `OI Zone Hi`: `Net_Pct_of_OI.expanding(min_periods=156).quantile(0.10 / 0.90)`
- `Crowded Signal`: +1 long, -1 short, 0 otherwise, using the default threshold of 90

NaN zones during warm-up make the comparisons False, so no signal. The latest `Crowded Signal` drives alerts and warnings. **Alternative:** compute in charts only; rejected because the alerts would then need a second copy of the logic.

### D2. Charts re-derive markers from carried columns, to honor the slider
The slider changes the rolling threshold, so the cached `Crowded Signal` (fixed at 90) cannot be used for markers. `data_processor` carries `OI Zone Lo/Hi` (and `_dxy` variants) through the merge. `build_comparison_chart` forms:
- long: `pct >= hi_thr` and `Net_Pct_of_OI >= OI Zone Hi`
- short: `pct <= 100 - hi_thr` and `Net_Pct_of_OI <= OI Zone Lo`

A shared helper `crowded_masks(pct, oi, zone_lo, zone_hi, threshold)` in `cftc_api.py` is used by both `calculate_crowded` and the chart, so the rule exists once.

### D3. Zone lines are traces, not rectangles
`_add_extreme_zones` currently draws flat `hrect`/`hline` at one level. Evolving lines need scatter traces: one dashed line for Hi and one for Lo, plus shading by `fill="tonexty"` is dropped (the lines are enough and cheaper). For the inverted USD Index panel, lines are `-Hi` and `-Lo`, relabeled so the upper line is `-Lo`. The Spread panel's zone uses an expanding quantile computed in the chart, since the spread is derived there.

### D4. Alerts
`ui_components._check_single_extreme` reads the latest `Crowded Signal` and shows "insufficient history" when the zone columns are NaN. The Extremes page gets a `Crowded` column from `_extreme_row`; `crowded_assets` filters on it instead of the percentile. The percentile column and its coloring stay, since it is still useful information.

### D5. Slider help text
The threshold slider and marker help strings are rewritten: the slider sets the stretch side only; the historical side is fixed at P90/P10.

## Risks / Trade-offs

- **Overlap with unarchived specs:** `positioning-charts` (marker trigger) and `sentiment-extremes-report` ("Crowded-trade warnings use only valid percentiles") are defined in `fix-bugs-and-optimize-app`. After that change is archived, those requirements need MODIFIED deltas that point to this capability. Until then they conflict only in trigger wording; orientation and NaN-handling rules remain true.
- **No signals before about 2009:** accepted; shown as insufficient history.
- **Expanding quantile can drift slowly late in history:** accepted; it is the honest "known at that time" definition.
- **Fewer markers can look broken:** the README and help text explain the rule.

## Migration Plan

No data migration. Roll back with `git revert`.
