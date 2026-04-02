import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from cftc_api import get_cot_data
from mt5_api import get_forex_data

# Dictionary mapping COT names to MT5 symbols (Removed USD INDEX / DXY logic)
COT_TO_MT5 = {
    'EURO FX': 'EURUSD',
    'BRITISH POUND': 'GBPUSD',
    'JAPANESE YEN': 'USDJPY',
    'SWISS FRANC': 'USDCHF',
    'CANADIAN DOLLAR': 'USDCAD',
    'AUSTRALIAN DOLLAR': 'AUDUSD',
    'NZ DOLLAR': 'NZDUSD'
}

def plot_cot_with_dxy(cot_name: str, num_bars: int = 1000, height: int = 900):
    """
    Plots a triple-subplot interactive chart:
    - Top: MT5 Close Price
    - Middle: CFTC Net Speculative Position for the selected currency
    - Bottom: CFTC Net Speculative Position for the USD INDEX
    """
    cot_name_upper = cot_name.upper()
    if cot_name_upper not in COT_TO_MT5:
        mt5_symbol = cot_name_upper
    else:
        mt5_symbol = COT_TO_MT5[cot_name_upper]

    print(f"[1/3] Fetching MT5 Data for {mt5_symbol}...")
    df_mt5 = get_forex_data(mt5_symbol, timeframe="W1", num_bars=num_bars)

    print(f"[2/3] Fetching COT Data for {cot_name_upper}...")
    df_cot = get_cot_data(cot_name_upper)

    print(f"[3/3] Fetching COT Data for USD INDEX...")
    df_dxy_cot = get_cot_data('USD INDEX')

    if df_mt5.empty:
        print(f"No MT5 data found for {mt5_symbol}.")
        return None
    if df_cot.empty:
        print(f"No COT data found for {cot_name_upper}.")
        return None
    if df_dxy_cot.empty:
        print(f"No COT data found for USD INDEX.")
        return None

    # Check if this pair needs price inversion (USD base currency)
    invert_price = mt5_symbol in ['USDJPY', 'USDCHF', 'USDCAD']
    axis_title_note = " (Inverted Axis)" if invert_price else ""

    # Create figure with 3 stacked subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            f"<b>{mt5_symbol} Weekly Close</b>",
            f"<b>{cot_name_upper} Net Speculative Position</b>",
            "<b>USD INDEX Net Speculative Position</b>"
        )
    )

    # 1. Top Subplot: MT5 Close Price Trace (Line)
    fig.add_trace(
        go.Scatter(
            x=df_mt5.index,
            y=df_mt5['close'],
            mode='lines',
            name=f'{mt5_symbol}',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )

    # 2. Middle Subplot: CFTC Net Speculative Position Trace (Bars, green/red)
    colors_main = ['green' if val >= 0 else 'red' for val in df_cot['Net Position']]
    fig.add_trace(
        go.Bar(
            x=df_cot['Date'],
            y=df_cot['Net Position'],
            name=f'{cot_name_upper} COT',
            marker_color=colors_main,
            opacity=0.7
        ),
        row=2, col=1
    )

    # 3. Bottom Subplot: USD INDEX Net Speculative Position Trace (Bars, blue)
    fig.add_trace(
        go.Bar(
            x=df_dxy_cot['Date'],
            y=df_dxy_cot['Net Position'],
            name='USD INDEX COT',
            marker_color='dodgerblue',
            opacity=0.7
        ),
        row=3, col=1
    )

    # Layout Formatting
    fig.update_layout(
        height=height,
        hovermode="x unified",
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # Set y-axes titles
    fig.update_yaxes(title_text=f"<b>Price</b>{axis_title_note}", row=1, col=1)
    fig.update_yaxes(title_text="<b>Contracts</b>", row=2, col=1)
    fig.update_yaxes(title_text="<b>Contracts</b>", row=3, col=1)

    # Apply Inversion to visual alignment if necessary
    if invert_price:
        fig.update_yaxes(autorange="reversed", row=1, col=1)

    # Force x-axis to align limits sensibly across all 3 traces
    all_dates = list(df_mt5.index) + df_cot['Date'].tolist() + df_dxy_cot['Date'].tolist()
    if all_dates:
        fig.update_xaxes(range=[min(all_dates), max(all_dates)])

    return fig

if __name__ == "__main__":
    fig = plot_cot_with_dxy('EURO FX')
    if fig:
        fig.show()
