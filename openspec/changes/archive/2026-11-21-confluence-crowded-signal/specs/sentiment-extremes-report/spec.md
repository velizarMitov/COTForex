# Spec Delta

## MODIFIED Requirements

### Requirement: Report row content
Each selected asset SHALL get one row with: the latest report date, the current Net Position, the 52-week minimum and maximum of Net Position, the 52-week percentile, and a Crowded verdict (Long, Short, No, or Insufficient history). The min, max and percentile SHALL all use the same 52-week window and the same minimum-history rule.

#### Scenario: Min and max match the percentile window
- **WHEN** an asset's latest Net Position equals its reported 52W Max
- **THEN** its reported 52W percentile is 100

#### Scenario: USD Index included
- **WHEN** "Include USD INDEX" is checked
- **THEN** the report contains a USD Index row computed the same way as the pair rows

#### Scenario: Crowded verdict shown
- **WHEN** an asset's latest week is crowded short
- **THEN** its Crowded cell reads Short

### Requirement: Crowded-trade warnings use only valid percentiles
A crowded-long warning SHALL appear for each asset whose Crowded verdict is Long, and a crowded-short warning for each asset whose verdict is Short, as defined by the crowded-positioning-signal capability. An asset with a missing percentile SHALL get no warning and SHALL show its percentile as empty, not zero.

#### Scenario: Missing percentile
- **WHEN** an asset's percentile cannot be computed
- **THEN** its percentile cell is blank and no crowded-short warning is raised for it

#### Scenario: No extremes
- **WHEN** no selected asset has a Long or Short verdict
- **THEN** a single "no selected asset is crowded" success message is shown

#### Scenario: Stretched but not historically rare
- **WHEN** an asset's 52-week percentile is 100 but its Net % of OI is inside its historical zone
- **THEN** no warning is raised for it
