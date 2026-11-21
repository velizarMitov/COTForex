# Spec Delta

## Purpose

Defines the multi-asset Extremes & Comparison report: one row per selected asset with its latest positioning versus its 52-week range, crowded-trade warnings, and a CSV export of the same data.

## ADDED Requirements

### Requirement: Report row content
Each selected asset SHALL get one row with: the latest report date, the current Net Position, the 52-week minimum and maximum of Net Position, and the 52-week percentile. The min, max and percentile SHALL all use the same 52-week window and the same minimum-history rule.

#### Scenario: Min and max match the percentile window
- **WHEN** an asset's latest Net Position equals its reported 52W Max
- **THEN** its reported 52W percentile is 100

#### Scenario: USD Index included
- **WHEN** "Include USD INDEX" is checked
- **THEN** the report contains a USD Index row computed the same way as the pair rows

### Requirement: Crowded-trade warnings use only valid percentiles
A crowded-long warning SHALL appear for each asset whose percentile is at or above 90. A crowded-short warning SHALL appear for each asset at or below 10. An asset with a missing percentile SHALL get no warning and SHALL show its percentile as empty, not zero.

#### Scenario: Missing percentile
- **WHEN** an asset's percentile cannot be computed
- **THEN** its percentile cell is blank and no crowded-short warning is raised for it

#### Scenario: No extremes
- **WHEN** every selected asset's percentile is strictly between 10 and 90
- **THEN** a single "within normal bounds" success message is shown

### Requirement: CSV export matches the table
The CSV download SHALL contain exactly the rows and columns shown in the report table, with missing values left empty.

#### Scenario: Export after selection
- **WHEN** the user downloads the CSV
- **THEN** the file has one row per displayed asset and the same column headers as the table
