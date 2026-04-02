"""MetaTrader 5 API helpers for fetching historical forex data."""

import MetaTrader5 as mt5
import pandas as pd

def init_mt5() -> bool:
    """Initialize a connection to the MetaTrader 5 terminal."""
    if not mt5.initialize():
        print(f"MetaTrader5 initialization failed, error code={mt5.last_error()}")
        return False
    return True

def shutdown_mt5():
    """Shut down the MetaTrader 5 connection."""
    mt5.shutdown()

def get_forex_data(symbol: str, timeframe: str = "W1", num_bars: int = 1000) -> pd.DataFrame:
    """Fetch historical OHLC data from MetaTrader 5 and isolate the 'close' price.

    Args:
        symbol: The Forex pair string (e.g., 'EURUSD', 'GBPUSD').
        timeframe: A friendly timeframe string, e.g., 'W1' for weekly, 'D1' for daily. Default: 'W1'.
        num_bars: The number of historical bars to retrieve.

    Returns:
        A pandas DataFrame indexed by datetime containing the 'close' column.
        Returns an empty DataFrame if MT5 fails or no data is found.
    """
    if not init_mt5():
        return pd.DataFrame()

    # Map readable timeframe inputs to MT5 internal constants
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }

    tf_value = tf_map.get(timeframe.upper().strip(), mt5.TIMEFRAME_W1)

    # Ensure the symbol is active in "Market Watch" before fetching
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol '{symbol}' not found on the active MT5 server.")
        return pd.DataFrame()

    # Fetch historical bars (from latest backwards)
    rates = mt5.copy_rates_from_pos(symbol, tf_value, 0, num_bars)

    if rates is None or len(rates) == 0:
        print(f"No rates found for {symbol}. Error code={mt5.last_error()}")
        return pd.DataFrame()

    # Create the pandas DataFrame from the structured array
    df = pd.DataFrame(rates)

    # Convert the integer 'time' (seconds since epoch) to a DatetimeIndex
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    # Note: Rates usually have columns: 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume'
    # Per requirements, isolate the 'close' price. (Other OHLC fields are dropped).
    result = df[["close"]].copy()

    return result

