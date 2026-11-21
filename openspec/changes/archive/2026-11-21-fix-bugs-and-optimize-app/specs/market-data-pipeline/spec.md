# Spec Delta

## Purpose

Provides CFTC Traders in Financial Futures positioning data and MT5 weekly prices to the dashboard. It derives positioning metrics, aligns both sources on a common weekly timeline, and reports clearly which source failed.

## ADDED Requirements

### Requirement: Positioning metrics stay row-aligned
For every CFTC report row, the derived Net Position, Net % of OI, week-over-week change and 52-week percentile SHALL come from that same row's long and short values. They SHALL stay aligned even when invalid rows are dropped or the source rows arrive out of date order.

#### Scenario: Source rows arrive unsorted
- **WHEN** the CFTC response lists report dates out of chronological order
- **THEN** the output is sorted by date, and each row's Net % of OI equals that row's long % of OI minus its short % of OI

#### Scenario: A row with an invalid date is dropped
- **WHEN** one CFTC row has an unparseable report date
- **THEN** that row is excluded, and every remaining row's Net % of OI still matches its own long and short percentages

### Requirement: 52-week percentile requires sufficient history
The 52-week percentile SHALL be the rolling min-max rank of Net Position over 52 weeks. Before 26 weeks of history exist, or when the 52-week range is flat, it SHALL be reported as neutral (50).

#### Scenario: Early history is neutral
- **WHEN** fewer than 26 weekly reports precede a row
- **THEN** that row's 52-week percentile is 50

#### Scenario: Flat range is neutral
- **WHEN** Net Position is identical across the whole window
- **THEN** the 52-week percentile is 50

### Requirement: Fetched data is cached between interactions
CFTC and MT5 results SHALL be reused across dashboard interactions for a bounded time. Changing chart options, display modes or pages SHALL NOT trigger a new network request or terminal call while cached data is still fresh.

#### Scenario: Toggling a chart option
- **WHEN** a user changes a chart option after the data has loaded once
- **THEN** the dashboard re-renders without refetching CFTC or MT5 data

#### Scenario: Cache expiry
- **WHEN** the cache lifetime has passed since the last fetch for a market
- **THEN** the next request for that market fetches fresh data

#### Scenario: Failed fetch is not cached
- **WHEN** a CFTC or MT5 fetch fails or returns no rows
- **THEN** the next interaction retries the fetch instead of reusing the empty result

### Requirement: Load failures identify their source
When aligned data cannot be produced, the dashboard SHALL tell the user which input failed: the selected pair's COT data, the USD Index COT data, the MT5 price data, or no overlapping dates between them.

#### Scenario: MT5 terminal unavailable
- **WHEN** COT data loads but the MT5 terminal is not running
- **THEN** the dashboard shows an error naming MT5 price data as the failed source

#### Scenario: No date overlap
- **WHEN** all three sources load but no COT report date falls within 6 days of an MT5 weekly bar
- **THEN** the dashboard shows an error saying the datasets do not overlap
