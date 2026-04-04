import streamlit as st

def render_momentum_metrics(df_mt5, df_cot, df_dxy, selected_pair, selected_cot_name):
    """Renders the top-level momentum metrics for price and commitments."""
    st.subheader("Weekly Momentum Metrics")
    col1, col2, col3 = st.columns(3)

    if len(df_mt5) >= 2:
        current_price, prev_price = df_mt5['close'].iloc[-1], df_mt5['close'].iloc[-2]
        price_change = current_price - prev_price
        price_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
        col1.metric(label=f"{selected_pair} Weekly Close", value=f"{current_price:.5f}", delta=f"{price_change:+.5f} ({price_pct:+.2f}%)")

    if not df_cot.empty:
        col2.metric(
            label=f"{selected_cot_name} Net Pos",
            value=f"{int(df_cot['Net Position'].iloc[-1]):,}",
            delta=f"{int(df_cot['Net Position Change'].iloc[-1]):+,} ({df_cot['Net Position % Change'].iloc[-1]:+.2f}%)"
        )

    if not df_dxy.empty:
        col3.metric(
            label="USD INDEX Net Pos",
            value=f"{int(df_dxy['Net Position'].iloc[-1]):,}",
            delta=f"{int(df_dxy['Net Position Change'].iloc[-1]):+,} ({df_dxy['Net Position % Change'].iloc[-1]:+.2f}%)"
        )


def _check_single_extreme(col_obj, name, cot_index):
    col_obj.write(f"**{name} 52-Week Percentile**: {cot_index:.1f}%")
    if cot_index >= 90:
        col_obj.error("Extreme Bullish Sentiment (>=90%) - Potential Crowded Long (Reversal Zone)")
    elif cot_index <= 10:
        col_obj.error("Extreme Bearish Sentiment (<=10%) - Potential Crowded Short (Reversal Zone)")
    else:
        col_obj.success("Neutral sentiment bounds within normal range.")


def render_sentiment_extremes(df_cot, df_dxy, selected_cot_name):
    """Renders the 52-week percentile alert panels."""
    st.subheader("Market Sentiment Extremes")
    ext1, ext2 = st.columns(2)
    if not df_cot.empty:
        _check_single_extreme(ext1, selected_cot_name, df_cot['52-Week Percentile'].iloc[-1])
    if not df_dxy.empty:
        _check_single_extreme(ext2, "USD INDEX", df_dxy['52-Week Percentile'].iloc[-1])

