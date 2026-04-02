import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from cftc_api import get_cot_data
from mt5_api import get_forex_data

# Dictionary mapping COT names to MT5 symbols
COT_TO_MT5 = {
    'EURO FX': 'EURUSD',
    'BRITISH POUND': 'GBPUSD',
    'JAPANESE YEN': 'USDJPY',
    'SWISS FRANC': 'USDCHF',
    'CANADIAN DOLLAR': 'USDCAD',
    'AUSTRALIAN DOLLAR': 'AUDUSD',
    'NZ DOLLAR': 'NZDUSD',
    'USD INDEX': 'DXY', # Or USDX depending on the broker
}

def plot_cot_vs_price(cot_name: str, num_bars: int = 1000):
    """
    Plots a dual-axis interactive chart:
    - Left Y-Axis: MT5 Close Price (Line)
    - Right Y-Axis: CFTC Net Speculative Position (Bar)

    Automatically inverts the left axis for USD-based pairs (JPY, CHF, CAD)
    since their prices are inverted compared to the COT futures data.
    """
    cot_name_upper = cot_name.upper()
    if cot_name_upper not in COT_TO_MT5:
        print(f"Creating implicit mapping for {cot_name_upper} (assuming MT5 symbol is identical)")
        mt5_symbol = cot_name_upper
    else:
        mt5_symbol = COT_TO_MT5[cot_name_upper]

    print(f"[1/2] Fetching COT Data for {cot_name_upper}...")
    df_cot = get_cot_data(cot_name_upper)

    print(f"[2/2] Fetching MT5 Data for {mt5_symbol}...")
    df_mt5 = get_forex_data(mt5_symbol, timeframe="W1", num_bars=num_bars)

    if df_cot.empty:
        print(f"No COT data found for {cot_name_upper}.")
        return

    if df_mt5.empty:
        print(f"No MT5 data found for {mt5_symbol}.")
        return

    # Check if this pair needs price inversion (USD base currency)
    invert_price = mt5_symbol in ['USDJPY', 'USDCHF', 'USDCAD']
    axis_title_note = " (Inverted Axis)" if invert_price else ""

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Add MT5 Close Price Trace (Line)
    fig.add_trace(
        go.Scatter(
            x=df_mt5.index,
            y=df_mt5['close'],
            mode='lines',
            name=f'{mt5_symbol} Weekly Close',
            line=dict(color='blue', width=2)
        ),
        secondary_y=False,
    )

    # 2. Add CFTC Net Speculative Position Trace (Bars)
    # Color code positive (green) and negative (red) net positions
    colors = ['green' if val >= 0 else 'red' for val in df_cot['Net Position']]

    fig.add_trace(
        go.Bar(
            x=df_cot['Date'],
            y=df_cot['Net Position'],
            name='Net Speculative Position',
            marker_color=colors,
            opacity=0.4
        ),
        secondary_y=True,
    )

    # 3. Layout Formatting
    title = f"<b>{mt5_symbol} Price vs {cot_name_upper} CFTC Net Speculative Position</b>"

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Set y-axes titles
    fig.update_yaxes(title_text=f"<b>MT5 Close Price</b>{axis_title_note}", secondary_y=False)
    fig.update_yaxes(title_text="<b>Net Speculative Position (Contracts)</b>", secondary_y=True)

    # Apply Inversion to visual alignment if necessary
    if invert_price:
        fig.update_yaxes(autorange="reversed", secondary_y=False)

    # Force x-axis to align limits sensibly based on overlapping data
    min_date = max(df_mt5.index.min(), df_cot['Date'].min())
    max_date = max(df_mt5.index.max(), df_cot['Date'].max())
    fig.update_xaxes(range=[min_date, max_date])

    print("Opening interactive chart in browser...")
    fig.show()

if __name__ == "__main__":
    # You can change the currency here to test others, e.g., 'JAPANESE YEN' or 'SWISS FRANC'
    plot_cot_vs_price('EURO FX')

