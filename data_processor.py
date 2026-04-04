import pandas as pd
from main import COT_TO_MT5
from cftc_api import get_cot_data
from mt5_api import get_forex_data

# Reverse dict for comparisons
mt5_to_cot = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}

def load_and_align_data(selected_pair: str, selected_cot_name: str, num_bars: int):
    """Fetches COT, DXY, and MT5 data, then aligns them perfectly by Date."""
    df_cot = get_cot_data(selected_cot_name)
    df_dxy = get_cot_data('USD INDEX')
    df_mt5 = get_forex_data(selected_pair, timeframe="W1", num_bars=num_bars)

    if df_cot.empty or df_mt5.empty or df_dxy.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_cot['Date'] = pd.to_datetime(df_cot['Date']).dt.tz_localize(None)
    df_dxy['Date'] = pd.to_datetime(df_dxy['Date']).dt.tz_localize(None)

    df_cot_merged = pd.merge(
        df_cot[['Date', 'Net Position', 'Net_Pct_of_OI']],
        df_dxy[['Date', 'Net Position', 'Net_Pct_of_OI']],
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

    return df_merged, df_cot, df_dxy, df_mt5


def get_comparison_data(selected_pairs_mt5, include_usd):
    """Fetches and calculates comparison extremes for multiple currencies."""
    results = []

    for mt5_sym in selected_pairs_mt5:
        cot_name = mt5_to_cot[mt5_sym]
        df = get_cot_data(cot_name)
        if not df.empty:
            latest = df.iloc[-1]
            roll_min_52 = df["Net Position"].rolling(window=52, min_periods=1).min().iloc[-1]
            roll_max_52 = df["Net Position"].rolling(window=52, min_periods=1).max().iloc[-1]
            results.append({
                "Asset": f"{mt5_sym} ({cot_name})",
                "Date": latest["Date"].strftime("%Y-%m-%d"),
                "Current Net Pos": int(latest["Net Position"]),
                "52W Min": int(roll_min_52),
                "52W Max": int(roll_max_52),
                "52W Percentile (%)": round(latest["52-Week Percentile"], 2)
            })

    if include_usd:
        df_usd = get_cot_data("USD INDEX")
        if not df_usd.empty:
            latest_usd = df_usd.iloc[-1]
            r_min = df_usd["Net Position"].rolling(window=52, min_periods=1).min().iloc[-1]
            r_max = df_usd["Net Position"].rolling(window=52, min_periods=1).max().iloc[-1]
            results.append({
                "Asset": "DXY (USD INDEX)",
                "Date": latest_usd["Date"].strftime("%Y-%m-%d"),
                "Current Net Pos": int(latest_usd["Net Position"]),
                "52W Min": int(r_min),
                "52W Max": int(r_max),
                "52W Percentile (%)": round(latest_usd["52-Week Percentile"], 2)
            })

    return pd.DataFrame(results)

