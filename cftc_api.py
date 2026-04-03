"""CFTC Traders in Financial Futures (TFF) helpers.

This module fetches historical COT data from the official CFTC Socrata
endpoint and computes net speculative positioning for leveraged funds.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List
from urllib.error import HTTPError, URLError
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

    retries = 3
    for attempt in range(retries):
        try:
            with urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # Retry transient upstream/server errors.
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except URLError:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise

    return []


def fetch_cftc_data(symbol: str) -> pd.DataFrame:
    """Only handles the API request and returns a raw DataFrame with basic Date and Net Position."""
    market_name = _normalize_currency_name(symbol)
    rows = _fetch_rows(market_name)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"], errors="coerce")
    long_col = pd.to_numeric(df.get("lev_money_positions_long"), errors="coerce").fillna(0)
    short_col = pd.to_numeric(df.get("lev_money_positions_short"), errors="coerce").fillna(0)
    df["Net Position"] = long_col - short_col

    result = df.dropna(subset=["Date", "Net Position"]).sort_values("Date").reset_index(drop=True)
    
    # Store other columns just in case
    for col in ["pct_of_oi_lev_money_long", "pct_of_oi_lev_money_short"]:
        if col in df.columns:
            result[col] = df[col]
            
    return result


def calculate_open_interest(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the Net_Pct_of_OI."""
    if df.empty:
        return df
    long_pct_col = pd.to_numeric(df.get("pct_of_oi_lev_money_long"), errors="coerce").fillna(0)
    short_pct_col = pd.to_numeric(df.get("pct_of_oi_lev_money_short"), errors="coerce").fillna(0)
    df["Net_Pct_of_OI"] = long_pct_col - short_pct_col
    return df


def calculate_momentum_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the week-over-week changes (absolute and %)."""
    if df.empty or "Net Position" not in df.columns:
        return df
    
    prev_pos = df["Net Position"].shift(1)
    df["Net Position Change"] = df["Net Position"] - prev_pos
    df["Net Position Change"] = df["Net Position Change"].fillna(0)

    # Use abs() on the denominator
    pct_change = (df["Net Position Change"] / prev_pos.abs()) * 100
    df["Net Position % Change"] = pct_change.replace([float('inf'), float('-inf')], 0).fillna(0)
    return df


def calculate_extremes(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the 52-week percentiles based on Net Position."""
    if df.empty or "Net Position" not in df.columns:
        return df
        
    roll_min = df["Net Position"].rolling(window=52, min_periods=1).min()
    roll_max = df["Net Position"].rolling(window=52, min_periods=1).max()
    
    percentile = ((df["Net Position"] - roll_min) / (roll_max - roll_min)) * 100
    df["52-Week Percentile"] = percentile.fillna(50)
    return df


def get_cot_data(currency_name: str) -> pd.DataFrame:
    """Wrapper to maintain compatibility."""
    empty = pd.DataFrame(
        columns=[
            "Date",
            "Net Position",
            "Net_Pct_of_OI",
            "Net Position Change",
            "Net Position % Change",
            "52-Week Percentile",
        ]
    )

    try:
        df = fetch_cftc_data(currency_name)
    except Exception as exc:
        # Keep Streamlit app alive when CFTC endpoint is temporarily unstable.
        print(f"CFTC fetch failed for '{currency_name}': {exc}")
        return empty

    if df.empty:
        return empty

    df = calculate_open_interest(df)
    df = calculate_momentum_metrics(df)
    df = calculate_extremes(df)
    return df
