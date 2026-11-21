import streamlit as st

from cftc_api import crowded_verdict
from symbols import price_decimals

def render_momentum_metrics(df_mt5, df_cot, df_dxy, selected_pair, selected_cot_name):
    """Renders the top-level momentum metrics for price and commitments."""
    st.subheader("Weekly Momentum Metrics")
    col1, col2, col3 = st.columns(3)

    if len(df_mt5) >= 2:
        current_price, prev_price = df_mt5['close'].iloc[-1], df_mt5['close'].iloc[-2]
        price_change = current_price - prev_price
        price_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
        dec = price_decimals(selected_pair)
        col1.metric(label=f"{selected_pair} Weekly Close", value=f"{current_price:.{dec}f}", delta=f"{price_change:+.{dec}f} ({price_pct:+.2f}%)")

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


def _check_single_extreme(col_obj, name, latest):
    pct, oi = latest["52-Week Percentile"], latest["Net_Pct_of_OI"]
    col_obj.write(f"**{name}** - 52-week percentile: {pct:.0f}% | Net OI: {oi:+.1f}%")
    verdict = crowded_verdict(latest)
    if verdict == "long":
        col_obj.error("Crowded Long - stretched vs last year and above its historical P90 (reversal risk)")
    elif verdict == "short":
        col_obj.error("Crowded Short - stretched vs last year and below its historical P10 (reversal risk)")
    elif verdict == "warmup":
        col_obj.info("Not enough history yet to judge (needs about 3 years of reports).")
    else:
        col_obj.success("Not crowded: positioning is not at a historical extreme.")


def render_sentiment_extremes(df_cot, df_dxy, selected_cot_name):
    """Renders the crowded-positioning alert panels."""
    st.subheader("Market Sentiment Extremes")
    ext1, ext2 = st.columns(2)
    if not df_cot.empty:
        _check_single_extreme(ext1, selected_cot_name, df_cot.iloc[-1])
    if not df_dxy.empty:
        _check_single_extreme(ext2, "USD INDEX", df_dxy.iloc[-1])

