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
            "lev_money_positions_short"
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

    result = (
        df[["Date", "Net Position"]]
        .dropna(subset=["Date", "Net Position"])
        .sort_values("Date")
        .reset_index(drop=True)
    )
    return result

