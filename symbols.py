"""CFTC market name <-> MT5 symbol mapping for the supported pairs."""

COT_TO_MT5 = {
    "EURO FX": "EURUSD",
    "BRITISH POUND": "GBPUSD",
    "JAPANESE YEN": "USDJPY",
    "SWISS FRANC": "USDCHF",
    "CANADIAN DOLLAR": "USDCAD",
    "AUSTRALIAN DOLLAR": "AUDUSD",
    "NZ DOLLAR": "NZDUSD",
    "GOLD": "XAUUSD",
}

MT5_TO_COT = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}


def price_decimals(symbol: str) -> int:
    """Decimals to show for a price: gold 2, JPY pairs 3, everything else 5."""
    symbol = symbol.upper()
    if symbol.startswith("XAU"):
        return 2
    return 3 if symbol.endswith("JPY") else 5
