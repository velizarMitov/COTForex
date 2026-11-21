# Spec Delta

## ADDED Requirements

### Requirement: Gold positioning comes from the Managed Money category
Gold futures positioning SHALL come from the CFTC Disaggregated Futures Only report for COMEX gold, using the Managed Money long and short positions. It SHALL be exposed with the same derived metrics as every other market: Net Position, Net % of OI, week-over-week change, 52-week percentile, historical zone and crowded verdict.

#### Scenario: Gold metrics match currency metrics
- **WHEN** gold COT data is loaded
- **THEN** it contains the same derived columns as a currency market, and Net Position equals Managed Money long minus short for each report date

#### Scenario: Gold is an accepted market name
- **WHEN** a caller asks for COT data using "GOLD" or "XAUUSD"
- **THEN** the gold data is returned instead of an unsupported-market error

### Requirement: MT5 symbol names are resolved per broker
When the app asks for an instrument whose broker name varies, it SHALL try the known alternative names against the connected MT5 terminal and use the first that exists. If none exists, it SHALL report the price data as unavailable.

#### Scenario: Broker calls gold GOLD
- **WHEN** XAUUSD is requested and the terminal has a symbol named GOLD but none named XAUUSD
- **THEN** prices are fetched from GOLD

#### Scenario: No matching symbol
- **WHEN** none of the alternative names exists on the terminal
- **THEN** the dashboard shows the MT5 price data as unavailable for that instrument
