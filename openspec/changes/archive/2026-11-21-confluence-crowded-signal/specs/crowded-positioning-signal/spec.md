# Spec Delta

## Purpose

Defines when leveraged-fund positioning counts as crowded: stretched against the last year and rare against all history known at that time. It also defines how that one definition drives markers, zone lines, alerts and warnings.

## ADDED Requirements

### Requirement: Historical zone uses only past data
For each week, the historical zone SHALL be the 10th and 90th percentile of Net % of OI over all reports up to and including that week. It SHALL NOT use later reports. No zone SHALL exist until 156 weekly reports are available.

#### Scenario: Later data does not change past zones
- **WHEN** newer weekly reports are appended to the history
- **THEN** the zone values for every earlier week are unchanged

#### Scenario: Warm-up period
- **WHEN** fewer than 156 weekly reports precede and include a given week
- **THEN** that week has no historical zone and no crowded signal

### Requirement: Crowded signal requires confluence
A week SHALL be crowded long only if its 52-week percentile is at or above the extreme threshold and its Net % of OI is at or above that week's historical P90. A week SHALL be crowded short only if the percentile is at or below 100 minus the threshold and Net % of OI is at or below that week's historical P10.

#### Scenario: Stretched but not historically rare
- **WHEN** a market's 52-week percentile is 100 but its Net % of OI lies between its historical P10 and P90
- **THEN** the week is not crowded

#### Scenario: Historically rare but not stretched
- **WHEN** Net % of OI is beyond its historical P90 but the 52-week percentile is below the threshold
- **THEN** the week is not crowded

#### Scenario: Both agree
- **WHEN** the percentile is at or above the threshold and Net % of OI is at or above the historical P90
- **THEN** the week is crowded long

### Requirement: Markers follow the crowded signal
Extreme markers on the price panel SHALL appear only on crowded weeks, and the existing density controls (first touch, cooldown) SHALL apply to those weeks. The extreme-threshold slider SHALL adjust only the 52-week percentile side.

#### Scenario: No signal, no marker
- **WHEN** a week is stretched on the 52-week percentile but not crowded
- **THEN** no marker is drawn for that week

#### Scenario: Slider changes only the percentile side
- **WHEN** the user raises the extreme threshold
- **THEN** the historical P90/P10 definition is unchanged

### Requirement: Zone lines match the signal
When extreme zones are shown, the OI panels SHALL draw the same evolving P90/P10 lines used by the signal, with no zone drawn during warm-up. The inverted USD Index panel SHALL swap and negate its lines so they match its plotted values.

#### Scenario: Evolving lines
- **WHEN** the Comparison view shows extreme zones for a market whose historical P90 has changed over time
- **THEN** the drawn P90 line changes over time rather than being one flat level

#### Scenario: Inverted USD Index panel
- **WHEN** the USD Index panel is inverted
- **THEN** its upper line equals the negated historical P10 of the USD Index

### Requirement: Alerts and warnings use the crowded signal
The sentiment alerts on the Main page and the crowded-trade warnings on the Extremes page SHALL report Extreme Bullish only for the latest week being crowded long, and Extreme Bearish only for crowded short. During warm-up they SHALL show that history is insufficient instead of a neutral verdict.

#### Scenario: Latest week stretched but not rare
- **WHEN** the latest 52-week percentile is 1 but Net % of OI is inside the historical zone
- **THEN** no bearish alert or warning is shown for that asset

#### Scenario: Latest week crowded
- **WHEN** the latest week is crowded short
- **THEN** an Extreme Bearish alert is shown for that asset
