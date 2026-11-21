# Spec Delta

## MODIFIED Requirements

### Requirement: Extreme markers point in the pair's expected reversal direction
Crowded-positioning markers on the price panel SHALL point in the direction the displayed pair is expected to move if the crowded currency position unwinds. When USD is the pair's base currency, the direction SHALL be the opposite of the futures positioning. A week is crowded as defined by the crowded-positioning-signal capability.

#### Scenario: Crowded long on a USD-quote pair
- **WHEN** EURUSD is displayed and EUR futures positioning is crowded long
- **THEN** a red downward marker is drawn above the price at that week

#### Scenario: Crowded long on a USD-base pair
- **WHEN** USDJPY is displayed and JPY futures positioning is crowded long
- **THEN** a green upward marker is drawn below the price at that week

#### Scenario: Crowded short on a USD-base pair
- **WHEN** USDCHF is displayed and CHF futures positioning is crowded short
- **THEN** a red downward marker is drawn above the price at that week

#### Scenario: Marker label names the futures positioning
- **WHEN** a user hovers over any extreme marker
- **THEN** the label states the crowded futures side (for example, "Crowded LONG Japanese Yen futures") so the signal source is unambiguous
