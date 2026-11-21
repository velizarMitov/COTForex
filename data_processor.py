from typing import NamedTuple, Optional

import pandas as pd
import streamlit as st

from symbols import MT5_TO_COT as mt5_to_cot
from cftc_api import get_cot_data
from mt5_api import get_forex_data


class _EmptyResult(Exception):
    """Raised inside cached loaders so st.cache_data never stores a failed fetch."""


@st.cache_data(ttl="6h", show_spinner=False)
def _cot(cot_name: str) -> pd.DataFrame:
    df = get_cot_data(cot_name)
    if df.empty:
        raise _EmptyResult(cot_name)
    return df


@st.cache_data(ttl="15m", show_spinner=False)
def _prices(symbol: str, num_bars: int) -> pd.DataFrame:
    df = get_forex_data(symbol, timeframe="W1", num_bars=num_bars)
    if df.empty:
        raise _EmptyResult(symbol)
    return df


def _load(loader, *args) -> pd.DataFrame:
    try:
        return loader(*args)
    except _EmptyResult:
        return pd.DataFrame()


class AlignedData(NamedTuple):
    merged: pd.DataFrame
    cot: pd.DataFrame
    dxy: pd.DataFrame
    mt5: pd.DataFrame
    error: Optional[str]


def _failed(error: str) -> AlignedData:
    empty = pd.DataFrame()
    return AlignedData(empty, empty, empty, empty, error)


def load_and_align_data(selected_pair: str, selected_cot_name: str, num_bars: int) -> AlignedData:
    """Fetches COT, DXY, and MT5 data, then aligns them by Date."""
    df_cot = _load(_cot, selected_cot_name)
    if df_cot.empty:
        return _failed(f"COT data for {selected_cot_name} unavailable")
    df_dxy = _load(_cot, "USD INDEX")
    if df_dxy.empty:
        return _failed("USD Index COT data unavailable")
    df_mt5 = _load(_prices, selected_pair, num_bars)
    if df_mt5.empty:
        return _failed(f"MT5 price data for {selected_pair} unavailable (is the terminal running and logged in?)")

    df_cot['Date'] = pd.to_datetime(df_cot['Date']).dt.tz_localize(None)
    df_dxy['Date'] = pd.to_datetime(df_dxy['Date']).dt.tz_localize(None)

    # Carry the percentile through so charts can mark positioning extremes.
    merge_cols = ['Date', 'Net Position', 'Net_Pct_of_OI', '52-Week Percentile']
    cot_cols = [c for c in merge_cols if c in df_cot.columns]
    dxy_cols = [c for c in merge_cols if c in df_dxy.columns]

    df_cot_merged = pd.merge(
        df_cot[cot_cols],
        df_dxy[dxy_cols],
        on='Date', how='inner', suffixes=('', '_dxy')
    ).sort_values('Date')

    df_mt5_reset = df_mt5.reset_index()
    if 'time' in df_mt5_reset.columns:
        df_mt5_reset = df_mt5_reset.rename(columns={'time': 'Date'})
    df_mt5_reset['Date'] = pd.to_datetime(df_mt5_reset['Date']).dt.tz_localize(None)

    df_cot_merged['Date'] = df_cot_merged['Date'].astype('datetime64[ns]').dt.floor('s')
    df_mt5_reset['Date'] = df_mt5_reset['Date'].astype('datetime64[ns]').dt.floor('s')

    df_mt5_reset = df_mt5_reset.sort_values('Date')

    df_merged = pd.merge_asof(
        df_cot_merged,
        df_mt5_reset,
        on='Date',
        direction='nearest',
        tolerance=pd.Timedelta(days=6)
    ).dropna(subset=['close'])

    if df_merged.empty:
        return _failed("No overlapping dates between COT and MT5 data")

    return AlignedData(df_merged, df_cot, df_dxy, df_mt5, None)


def _int_or_none(value):
    return None if pd.isna(value) else int(value)


def _extreme_row(label: str, df: pd.DataFrame) -> dict:
    latest = df.iloc[-1]
    pct = latest["52-Week Percentile"]
    return {
        "Asset": label,
        "Date": latest["Date"].strftime("%Y-%m-%d"),
        "Current Net Pos": _int_or_none(latest["Net Position"]),
        "52W Min": _int_or_none(latest["52W Min"]),
        "52W Max": _int_or_none(latest["52W Max"]),
        "52W Percentile (%)": None if pd.isna(pct) else round(float(pct), 2),
    }


def get_comparison_data(selected_pairs_mt5, include_usd):
    """Latest 52-week positioning snapshot for each selected asset."""
    assets = [(f"{sym} ({mt5_to_cot[sym]})", mt5_to_cot[sym]) for sym in selected_pairs_mt5]
    if include_usd:
        assets.append(("DXY (USD INDEX)", "USD INDEX"))

    rows = []
    for label, cot_name in assets:
        df = _load(_cot, cot_name)
        if not df.empty:
            rows.append(_extreme_row(label, df))
    return pd.DataFrame(rows)
