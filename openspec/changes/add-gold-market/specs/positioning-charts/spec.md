# Spec Delta

## ADDED Requirements

### Requirement: Prices use instrument-appropriate precision
Price values in charts, hover labels and metric tiles SHALL use 2 decimals for gold, 3 for JPY pairs and 5 for all other pairs.

#### Scenario: Gold price
- **WHEN** XAUUSD is displayed with a latest close of 4012.3456
- **THEN** the weekly-close metric reads 4012.35

#### Scenario: JPY pair price
- **WHEN** USDJPY is displayed with a latest close of 150.1234
- **THEN** the weekly-close metric reads 150.123

### Requirement: Gold shows a positioning-category notice
Wherever gold is the selected instrument, the dashboard SHALL state that gold uses the Managed Money category while currencies use Leveraged Funds, so their levels are not directly comparable.

#### Scenario: Gold selected
- **WHEN** the user selects XAUUSD on the Main or Open Interest page
- **THEN** a notice about the Managed Money category is visible

#### Scenario: Currency selected
- **WHEN** the user selects a currency pair
- **THEN** no such notice is shown
