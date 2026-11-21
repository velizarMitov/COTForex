"""MetaTrader 5 API helpers for fetching historical forex data."""

import MetaTrader5 as mt5
import pandas as pd

def init_mt5_connection() -> bool:
    """Initialize a connection to the MetaTrader 5 terminal."""
    if not mt5.initialize():
        print(f"MetaTrader5 initialization failed, error code={mt5.last_error()}")
        return False
    return True

def shutdown_mt5():
    """Shut down the MetaTrader 5 connection."""
    mt5.shutdown()

# Brokers name some instruments differently; the first alias that exists wins.
SYMBOL_ALIASES = {
    "XAUUSD": ["XAUUSD", "GOLD", "XAUUSD.m", "XAUUSD.", "GOLD.", "XAUUSD#"],
}


def resolve_symbol(symbol: str):
    """The broker's name for ``symbol``, or None when the terminal has no match."""
    for candidate in SYMBOL_ALIASES.get(symbol.upper(), [symbol]):
        if mt5.symbol_info(candidate) is not None:
            return candidate

    # Last resort for suffixed names (e.g. "XAUUSD_i"); only exact-prefix matches count.
    if symbol.upper() in SYMBOL_ALIASES:
        for info in mt5.symbols_get(f"*{symbol.upper()}*") or []:
            if info.name.upper().startswith(symbol.upper()):
                return info.name
    return None


def fetch_forex_data(symbol: str, timeframe: str = "W1", num_bars: int = 1000) -> pd.DataFrame:
    """Fetch historical OHLC data from MetaTrader 5 and isolate the 'close' price.

    Args:
        symbol: The Forex pair string (e.g., 'EURUSD', 'GBPUSD').
        timeframe: A friendly timeframe string, e.g., 'W1' for weekly, 'D1' for daily. Default: 'W1'.
        num_bars: The number of historical bars to retrieve.

    Returns:
        A pandas DataFrame indexed by datetime containing the 'close' column.
        Returns an empty DataFrame if MT5 fails or no data is found.
    """
    if not init_mt5_connection():
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

    broker_symbol = resolve_symbol(symbol)
    if broker_symbol is None:
        print(f"Symbol '{symbol}' not found on the active MT5 server.")
        return pd.DataFrame()
    symbol = broker_symbol

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

def get_forex_data(symbol: str, timeframe: str = "W1", num_bars: int = 1000) -> pd.DataFrame:
    """Wrapper function for backwards compatibility."""
    return fetch_forex_data(symbol, timeframe, num_bars)
