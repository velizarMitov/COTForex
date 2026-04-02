"""CFTC Traders in Financial Futures (TFF) helpers.

This module fetches historical COT data from the official CFTC Socrata
endpoint and computes net speculative positioning for leveraged funds.
"""

from __future__ import annotations

import json
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

# Official CFTC Socrata dataset for "TFF - Futures Only".
_BASE_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

# Canonical market names in CFTC TFF Futures Only data.
_CURRENCY_MARKETS: Dict[str, str] = {
    "EURO FX": "EURO FX",
    "EUR": "EURO FX",
    "EURUSD": "EURO FX",
    "EUR/USD": "EURO FX",
    "BRITISH POUND": "BRITISH POUND",
    "BRITISH POUND STERLING": "BRITISH POUND",
    "GBP": "BRITISH POUND",
    "GBPUSD": "BRITISH POUND",
    "GBP/USD": "BRITISH POUND",
    "JAPANESE YEN": "JAPANESE YEN",
    "JPY": "JAPANESE YEN",
    "USDJPY": "JAPANESE YEN",
    "USD/JPY": "JAPANESE YEN",
    "SWISS FRANC": "SWISS FRANC",
    "CHF": "SWISS FRANC",
    "USDCHF": "SWISS FRANC",
    "USD/CHF": "SWISS FRANC",
    "CANADIAN DOLLAR": "CANADIAN DOLLAR",
    "CAD": "CANADIAN DOLLAR",
    "USDCAD": "CANADIAN DOLLAR",
    "USD/CAD": "CANADIAN DOLLAR",
    "AUSTRALIAN DOLLAR": "AUSTRALIAN DOLLAR",
    "AUD": "AUSTRALIAN DOLLAR",
    "AUDUSD": "AUSTRALIAN DOLLAR",
    "AUD/USD": "AUSTRALIAN DOLLAR",
    "NEW ZEALAND DOLLAR": "NZ DOLLAR",
    "NZ DOLLAR": "NZ DOLLAR",
    "NZD": "NZ DOLLAR",
    "NZDUSD": "NZ DOLLAR",
    "NZD/USD": "NZ DOLLAR",
    "USD INDEX": "USD INDEX",
    "USD DOLLAR INDEX": "USD INDEX",
    "DXY": "USD INDEX",
    "USDX": "USD INDEX",
    "U.S. DOLLAR INDEX": "USD INDEX",
    "U.S. DOLLAR INDEX - ICE FUTURES U.S.": "USD INDEX",
}


def _normalize_currency_name(currency_name: str) -> str:
    if not isinstance(currency_name, str) or not currency_name.strip():
        raise ValueError("currency_name must be a non-empty string")

    key = currency_name.strip().upper()
    if key not in _CURRENCY_MARKETS:
        supported = sorted(
            {
                "EURO FX",
                "BRITISH POUND",
                "JAPANESE YEN",
                "SWISS FRANC",
                "CANADIAN DOLLAR",
                "AUSTRALIAN DOLLAR",
                "NEW ZEALAND DOLLAR",
                "USD INDEX",
            }
        )
        raise ValueError(
            f"Unsupported currency '{currency_name}'. Supported: {', '.join(supported)}"
        )

    return _CURRENCY_MARKETS[key]


def _fetch_rows(contract_market_name: str) -> List[dict]:
    params = {
        "$select": (
            "report_date_as_yyyy_mm_dd,"
            "lev_money_positions_long,"
            "lev_money_positions_short,"
            "pct_of_oi_lev_money_long,"
            "pct_of_oi_lev_money_short"
        ),
        "$where": f"contract_market_name = '{contract_market_name}'",
        "$order": "report_date_as_yyyy_mm_dd asc",
        "$limit": "50000",
    }
    url = f"{_BASE_URL}?{urlencode(params)}"

    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_cot_data(currency_name: str) -> pd.DataFrame:
    """Return historical net speculative positions for a currency market.

    Net Position = Leveraged Funds Long - Leveraged Funds Short.

    Args:
        currency_name: Currency/alias like "EURO FX", "GBP", "USD/JPY".

    Returns:
        pandas.DataFrame with columns: "Date", "Net Position".
    """
    market_name = _normalize_currency_name(currency_name)
    rows = _fetch_rows(market_name)

    if not rows:
        return pd.DataFrame(columns=["Date", "Net Position"])

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"], errors="coerce")
    long_col = pd.to_numeric(df["lev_money_positions_long"], errors="coerce")
    short_col = pd.to_numeric(df["lev_money_positions_short"], errors="coerce")
    df["Net Position"] = long_col - short_col

    # Open Interest % metrics
    long_pct_col = pd.to_numeric(df.get("pct_of_oi_lev_money_long"), errors="coerce").fillna(0)
    short_pct_col = pd.to_numeric(df.get("pct_of_oi_lev_money_short"), errors="coerce").fillna(0)
    df["Net_Pct_of_OI"] = long_pct_col - short_pct_col

    result = (
        df[["Date", "Net Position", "Net_Pct_of_OI"]]
        .dropna(subset=["Date", "Net Position"])
        .sort_values("Date")
        .reset_index(drop=True)
    )
    
    # Calculate Weekly Change and % Change safely
    prev_pos = result["Net Position"].shift(1)
    result["Net Position Change"] = result["Net Position"] - prev_pos
    
    # Use abs() on the denominator to preserve shift direction correctly if it crosses 0 or is negative
    result["Net Position % Change"] = (result["Net Position Change"] / prev_pos.abs()) * 100
    
    # Handle possible division by zero infinity and NaNs explicitly
    result["Net Position % Change"] = result["Net Position % Change"].replace([float('inf'), float('-inf')], 0).fillna(0)
    result["Net Position Change"] = result["Net Position Change"].fillna(0)

    # Calculate 52-Week Percentile
    roll_min = result["Net Position"].rolling(window=52, min_periods=1).min()
    roll_max = result["Net Position"].rolling(window=52, min_periods=1).max()
    
    # Safely calculate percentile
    result["52-Week Percentile"] = ((result["Net Position"] - roll_min) / (roll_max - roll_min)) * 100
    result["52-Week Percentile"] = result["52-Week Percentile"].fillna(50) # Default to neutral if max == min

    return result

