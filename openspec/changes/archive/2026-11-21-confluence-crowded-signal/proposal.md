# Proposal

## Why

The app uses two different ideas of "extreme" at once. Price-panel markers and "Extreme Bullish/Bearish" alerts use a rolling 52-week percentile of Net Position, which means "stretched versus the last year". The OI panels shade P10/P90 zones of the full history, which means "rare versus history". Measured on live data, 54-79% of markers sit where the panel underneath says "normal". Today EURUSD shows an "Extreme Bearish" alert at a Net OI of -8.8%, while the historical P10 line is at -27.9%.

The intended meaning of "crowded" is rare relative to history. The historical zones also use future data, so they would make past signals look smarter than they were.

## What Changes

- A "crowded" signal fires only when **both** hold: the 52-week percentile is stretched, and Net % of OI is beyond the historical P90/P10 as known **at that week** (expanding window, no look-ahead).
- The OI panels draw those same evolving P90/P10 lines instead of flat full-history lines, so markers and zones agree on screen.
- The "Extreme Bullish/Bearish" alerts (Main page) and crowded-trade warnings (Extremes page) use the same signal.
- Warm-up: no zones, markers or alerts until 156 weeks (about 3 years) of history exist; the first zones appear around mid-2009.
- Measured effect: about 45 markers per market over 20 years drops to about 12, and every market currently reads "normal".
- **BREAKING (visible behavior):** far fewer markers and alerts; nothing before about 2009.

**Out of scope:** changing the rolling percentile math, the threshold slider's range, the first-touch/cooldown logic, or any signal back-testing.

## Capabilities

### New Capabilities
- `crowded-positioning-signal`: Definition of a crowded long/short signal (confluence of rolling stretch and historical rarity), its warm-up, and how markers, zones, alerts and warnings present it.

### Modified Capabilities
_None as deltas, because `positioning-charts` and `sentiment-extremes-report` only exist inside the unarchived change `fix-bugs-and-optimize-app`. Once that change is archived, requirements there that this change supersedes must be reconciled (see design.md)._

## Impact

- **Code:** `cftc_api.py` (zone columns), `data_processor.py` (carry them through the merge; Extremes rows), `charts.py` (marker rule, zone lines), `ui_components.py` and `app.py` (alerts and warnings), tests.
- **Dependencies:** none.
- **Users:** fewer, rarer signals; sidebar slider help text changes.
