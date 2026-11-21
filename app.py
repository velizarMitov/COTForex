from typing import NamedTuple, Optional

import streamlit as st
import pandas as pd

from symbols import MT5_TO_COT
from data_processor import load_and_align_data, get_comparison_data
from charts import (
    build_overlay_chart,
    build_stacked_chart,
    build_comparison_chart,
    build_heatmap_chart,
    apply_shared_crosshair,
    PLOTLY_CONFIG,
)
from ui_components import render_momentum_metrics, render_sentiment_extremes

CHART_VIEWS = [
    "Comparison (Aligned)",
    "Stacked (one under another)",
    "Overlay",
    "Heatmap Analysis",
]


def _comparison_controls(key_prefix: str) -> dict:
    """Sidebar controls that only apply to the Comparison view."""
    st.sidebar.markdown("**Comparison options**")
    return {
        "invert_dxy": st.sidebar.toggle(
            "Invert USD Index panel",
            value=True,
            key=f"{key_prefix}_invert",
            help="Long EUR and short USD are the same trade. Inverting makes both "
                 "panels point the same way when positioning agrees.",
        ),
        "show_extreme_zones": st.sidebar.toggle(
            "Show extreme zones (P90 / P10)",
            value=True,
            key=f"{key_prefix}_zones",
        ),
        "show_extreme_markers": st.sidebar.toggle(
            "Mark extremes on price",
            value=True,
            key=f"{key_prefix}_markers",
            help="Triangles where the 52-week percentile crosses the threshold below.",
        ),
        "extreme_threshold": st.sidebar.slider(
            "Extreme threshold (percentile)",
            min_value=80, max_value=99, value=90, step=1,
            key=f"{key_prefix}_thr",
            help="90 means: positioning is in the top 10% or bottom 10% of its own "
                 "52-week range. Note this does NOT reduce the marker count much — a "
                 "rolling min-max percentile hits 100 on every new 52-week high, so a "
                 "higher threshold just fragments runs. Use Cooldown to thin them out.",
        ),
        "marker_mode": st.sidebar.radio(
            "Marker density",
            ["First touch only", "Every week"],
            index=0,
            horizontal=True,
            key=f"{key_prefix}_mdensity",
            help="A rolling min-max percentile prints 100 on every new 52-week high, "
                 "so a single trend fires for many consecutive weeks. 'First touch' "
                 "collapses each run to the week it entered the extreme.",
        ),
        "marker_cooldown": st.sidebar.slider(
            "Cooldown between markers (weeks)",
            min_value=0, max_value=26, value=8, step=1,
            key=f"{key_prefix}_cool",
            help="Suppresses a re-entry into the same extreme within this many weeks.",
        ),
        "show_extreme_shading": st.sidebar.toggle(
            "Shade extreme periods",
            value=False,
            key=f"{key_prefix}_shading",
            help="Off by default: the markers already flag the same events, and the "
                 "stripes make a 20-year view hard to read.",
        ),
        "corr_window": st.sidebar.slider(
            "Rolling correlation window (weeks)",
            min_value=8, max_value=104, value=26, step=2,
            key=f"{key_prefix}_corr",
        ),
    }


def _build_chart(mode, df_merged, selected_pair, selected_cot_name, date_density,
                 enable_crosshair, comparison_opts):
    if mode == "Overlay":
        return build_overlay_chart(df_merged, selected_pair, selected_cot_name, date_density)
    if mode == "Heatmap Analysis":
        return build_heatmap_chart(df_merged, selected_pair, selected_cot_name)
    if mode == "Comparison (Aligned)":
        return build_comparison_chart(
            df_merged, selected_pair, selected_cot_name, date_density,
            **(comparison_opts or {})
        )

    fig = build_stacked_chart(df_merged, selected_pair, selected_cot_name, date_density)
    if enable_crosshair:
        fig = apply_shared_crosshair(fig)
    return fig

mt5_to_cot = MT5_TO_COT
mt5_options = list(MT5_TO_COT)


def highlight_percentile(val):
    if pd.isna(val):
        return ''
    if val >= 90:
        return 'background-color: rgba(255, 99, 71, 0.4); color: white;'
    if val <= 10:
        return 'background-color: rgba(60, 179, 113, 0.4); color: white;'
    return ''


def crowded_assets(res_df: pd.DataFrame):
    """(crowded long rows, crowded short rows); NaN percentiles fall in neither."""
    pct = pd.to_numeric(res_df["52W Percentile (%)"], errors="coerce")
    return res_df[pct >= 90], res_df[pct <= 10]


class ChartSettings(NamedTuple):
    pair: str
    cot_name: str
    mode: str
    date_density: str
    crosshair: bool
    comparison_opts: Optional[dict]
    num_bars: int


def _chart_sidebar(key_prefix: str, header: str, view_label: str) -> ChartSettings:
    """Sidebar controls shared by every page that draws a price-vs-COT chart."""
    st.sidebar.header(header)

    pair = st.sidebar.selectbox("Select Currency Pair", mt5_options, key=f"{key_prefix}_pair")
    mode = st.sidebar.radio(
        view_label,
        CHART_VIEWS,
        index=0,
        key=f"{key_prefix}_chart_view",
        help="Comparison = aligned panels on a shared scale + spread & rolling correlation, "
             "Stacked = simple read, Overlay = one panel, Heatmap = correlation & seasonality",
    )
    date_density = st.sidebar.selectbox(
        "Date Axis Label Format",
        ["Auto", "1 Year", "2 Years", "Quarterly", "Monthly"],
        index=1,
        key=f"{key_prefix}_date_density",
        help="Select the density of the X-axis date labels.",
    )

    crosshair = False
    if mode == "Stacked (one under another)":
        crosshair = st.sidebar.toggle(
            "Enable vertical crosshair",
            value=True,
            key=f"{key_prefix}_crosshair",
            help="Displays a unified vertical line across all 3 stacked charts.",
        )

    comparison_opts = _comparison_controls(key_prefix) if mode == "Comparison (Aligned)" else None

    num_bars = st.sidebar.slider(
        "Number of Weekly Bars",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100,
        key=f"{key_prefix}_bars",
    )
    return ChartSettings(pair, mt5_to_cot[pair], mode, date_density, crosshair,
                         comparison_opts, num_bars)


def _settings_chart(s: ChartSettings, df_merged: pd.DataFrame):
    return _build_chart(s.mode, df_merged, s.pair, s.cot_name, s.date_density,
                        s.crosshair, s.comparison_opts)


# --- MAIN VIEW ROUTING ---
def render_main_dashboard():
    st.title("Forex COT vs Price Analysis")
    st.markdown("Compare MT5 Weekly Close Prices directly with specific currency COT **AND** the USD Index COT on a single timeline.")

    s = _chart_sidebar("main", "Settings", "Chart View")

    st.write(f"### Loading data for **{s.pair}** + **USD INDEX** COT ...")

    with st.spinner("Fetching data from CFTC and MT5..."):
        df_merged, df_cot, df_dxy, df_mt5, error = load_and_align_data(s.pair, s.cot_name, s.num_bars)

        if error:
            st.error(error)
        else:
            fig = _settings_chart(s, df_merged)

            render_momentum_metrics(df_mt5, df_cot, df_dxy, s.pair, s.cot_name)

            st.markdown("---")
            render_sentiment_extremes(df_cot, df_dxy, s.cot_name)
            st.markdown("---")

            st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def render_extremes_comparison():
    st.title("Market Sentiment Extremes & Comparison")
    st.markdown("Compare 52-Week Percentiles across multiple selected Forex pairs and the USD Index.")

    st.sidebar.header("Comparison Settings")
    # Default select first 3 pairs + we manually add USD INDEX below
    selected_pairs_mt5 = st.sidebar.multiselect("Select Forex Pairs", mt5_options, default=mt5_options[:3])
    include_usd = st.sidebar.checkbox("Include USD INDEX", value=True)

    if selected_pairs_mt5 or include_usd:
        with st.spinner("Fetching comparison data..."):
            res_df = get_comparison_data(selected_pairs_mt5, include_usd)

            if not res_df.empty:
                styled_df = (
                    res_df.style
                    .map(highlight_percentile, subset=["52W Percentile (%)"])
                    .format(na_rep="")
                )
                st.dataframe(styled_df, width="stretch")

                st.markdown("### Active Institutional Crowded Trade Warnings")
                bull_crowded, bear_crowded = crowded_assets(res_df)
                
                if bull_crowded.empty and bear_crowded.empty:
                    st.success("✅ All selected assets are currently within normal market bounds (between 10% and 90%).")
                else:
                    for _, row in bull_crowded.iterrows():
                        st.error(f"🚨 **{row['Asset']}** has an Extreme Bullish profile (**{row['52W Percentile (%)']}%**) - Heavy Long / Reversal Risk")
                    for _, row in bear_crowded.iterrows():
                        st.warning(f"📉 **{row['Asset']}** has an Extreme Bearish profile (**{row['52W Percentile (%)']}%**) - Heavy Short / Reversal Risk")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Export as CSV button
                csv_data = res_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Comparison Table (CSV)",
                    data=csv_data,
                    file_name="market_extremes_comparison.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data returned for selected assets.")

def render_open_interest_analysis():
    st.title("Open Interest Analysis")
    st.markdown("Analyze the net percentage of Open Interest (OI) held by leveraged speculative funds.")

    s = _chart_sidebar("oi", "OI Settings", "OI Chart View")

    with st.spinner("Fetching Open Interest and MT5 data..."):
        df_merged, _, _, _, error = load_and_align_data(s.pair, s.cot_name, s.num_bars)

        if error:
            st.error(error)
        else:
            st.plotly_chart(_settings_chart(s, df_merged), width="stretch", config=PLOTLY_CONFIG)

            st.markdown("### Latest Snapshot")
            latest = df_merged.iloc[-1]
            latest_oi = latest["Net_Pct_of_OI"]
            latest_dxy_oi = latest["Net_Pct_of_OI_dxy"]

            st.write(f"**Aligned Date:** {latest['Date'].strftime('%Y-%m-%d')}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(label=f"Current Price ({s.pair})", value=f"{latest['close']:.5f}")
            col2.metric(label=f"{s.cot_name} Net OI", value=f"{latest_oi:.2f}%")
            col3.metric(label="USD INDEX Net OI", value=f"{latest_dxy_oi:.2f}%")
            col4.metric(label="Spread (pair − USD)", value=f"{latest_oi - latest_dxy_oi:+.2f} pp")


def main():
    # Define Streamlit page basic setup
    st.set_page_config(
        page_title="COT & MT5 Forex Analysis",
        layout="wide",
        page_icon="📈"
    )

    # Navigation via sidebar
    page = st.sidebar.radio('Navigation', ['Main Dashboard', 'Extremes & Comparison', 'Open Interest Analysis'])
    st.sidebar.markdown("---")

    if page == 'Main Dashboard':
        render_main_dashboard()
    elif page == 'Extremes & Comparison':
        render_extremes_comparison()
    elif page == 'Open Interest Analysis':
        render_open_interest_analysis()

    st.sidebar.markdown("---")
    st.sidebar.info("Data sourced directly from **CFTC.gov** via Socrata API and local **MetaTrader 5** terminal.")

if __name__ == "__main__":
    main()
