"""CFTC market name <-> MT5 symbol mapping for the supported pairs."""

COT_TO_MT5 = {
    "EURO FX": "EURUSD",
    "BRITISH POUND": "GBPUSD",
    "JAPANESE YEN": "USDJPY",
    "SWISS FRANC": "USDCHF",
    "CANADIAN DOLLAR": "USDCAD",
    "AUSTRALIAN DOLLAR": "AUDUSD",
    "NZ DOLLAR": "NZDUSD",
}

MT5_TO_COT = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}
