import streamlit as st
import pandas as pd

from main import COT_TO_MT5
from data_processor import load_and_align_data, get_comparison_data
from charts import build_overlay_chart, build_stacked_chart, build_heatmap_chart, apply_shared_crosshair
from ui_components import render_momentum_metrics, render_sentiment_extremes

# Reverse the COT_TO_MT5 dict so we lookup COT names from MT5 symbols
mt5_to_cot = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}
mt5_options = list(mt5_to_cot.keys())



# --- MAIN VIEW ROUTING ---
def render_main_dashboard():
    st.title("Forex COT vs Price Analysis")
    st.markdown("Compare MT5 Weekly Close Prices directly with specific currency COT **AND** the USD Index COT on a single timeline.")

    # Create the sidebar for user inputs
    st.sidebar.header("Settings")

    selected_pair = st.sidebar.selectbox("Select Currency Pair", mt5_options)
    display_mode = st.sidebar.radio(
        "Chart View",
        ["Stacked (one under another)", "Overlay", "Heatmap Analysis"],
        index=0,
        help="Stacked = easier reading, Overlay = direct correlation view, Heatmap = professional correlation & seasonality",
    )


    date_density = st.sidebar.selectbox(
        "Date Axis Label Format",
        ["Auto", "1 Year", "2 Years", "Quarterly", "Monthly"],
        index=1,
        help="Select the density of the X-axis date labels."
    )

    enable_crosshair = False
    if display_mode == "Stacked (one under another)":
        enable_crosshair = st.sidebar.toggle(
            "Enable vertical crosshair",
            value=True,
            help="Displays a unified vertical line across all 3 stacked charts."
        )

    num_bars = st.sidebar.slider(
        "Number of Weekly Bars",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100
    )

    # Fetch the corresponding COT name from the selected MT5 ticker
    selected_cot_name = mt5_to_cot[selected_pair]

    st.write(f"### Loading data for **{selected_pair}** + **USD INDEX** COT ...")

    # Generate the chart
    with st.spinner("Fetching data from CFTC and MT5..."):
        df_merged, df_cot, df_dxy, df_mt5 = load_and_align_data(selected_pair, selected_cot_name, num_bars)

        if not df_merged.empty:
            if display_mode == "Overlay":
                fig = build_overlay_chart(df_merged, selected_pair, selected_cot_name, date_density)
            elif display_mode == "Heatmap Analysis":
                fig = build_heatmap_chart(df_merged, selected_pair, selected_cot_name)
            else:
                fig = build_stacked_chart(df_merged, selected_pair, selected_cot_name, date_density)
                if enable_crosshair:
                    fig = apply_shared_crosshair(fig)

            render_momentum_metrics(df_mt5, df_cot, df_dxy, selected_pair, selected_cot_name)

            st.markdown("---")
            render_sentiment_extremes(df_cot, df_dxy, selected_cot_name)
            st.markdown("---")

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to generate the chart. Please check terminal logs for details or if datasets overlap.")


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
                # Setup explicit Styler to highlight percentiles >=90 and <=10
                def highlight_percentile(val):
                    if isinstance(val, (int, float)):
                        if val >= 90:
                            return 'background-color: rgba(255, 99, 71, 0.4); color: white;' # Light Red
                        elif val <= 10:
                            return 'background-color: rgba(60, 179, 113, 0.4); color: white;' # Light Green
                    return ''
                
                # Explicitly fill any NaNs before styling to prevent errors
                res_df = res_df.fillna(0)
                styled_df = res_df.style.map(highlight_percentile, subset=["52W Percentile (%)"])
                
                # Render table
                st.dataframe(styled_df, use_container_width=True)
                
                # Check for explicit extremes and display warnings
                st.markdown("### Active Institutional Crowded Trade Warnings")
                bull_crowded = res_df[res_df["52W Percentile (%)"] >= 90]
                bear_crowded = res_df[res_df["52W Percentile (%)"] <= 10]
                
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

     st.sidebar.header("OI Settings")
     selected_pair = st.sidebar.selectbox("Select Currency Pair", mt5_options)
     selected_cot_name = mt5_to_cot[selected_pair]
     oi_display_mode = st.sidebar.radio(
         "OI Chart View",
         ["Stacked (one under another)", "Overlay", "Heatmap Analysis"],
         index=0,
         key="oi_chart_view",
         help="Stacked = clearer read, Overlay = compare on one panel, Heatmap = correlation & seasonality matrices",
     )

     date_density = st.sidebar.selectbox(
         "Date Axis Label Format",
         ["Auto", "1 Year", "2 Years", "Quarterly", "Monthly"],
         index=1,
         key="oi_date_density",
         help="Select the density of the X-axis date labels."
     )

     enable_crosshair_oi = False
     if oi_display_mode == "Stacked (one under another)":
         enable_crosshair_oi = st.sidebar.toggle(
             "Enable vertical crosshair",
             value=True,
             key="oi_crosshair",
             help="Displays a unified vertical line across all 3 stacked charts."
         )

     num_bars = st.sidebar.slider(
         "Number of Weekly Bars",
         min_value=100,
         max_value=2000,
         value=1000,
         step=100,
         key="oi_bars"
     )

     with st.spinner("Fetching Open Interest and MT5 data..."):
         df_merged, df_cot, df_dxy, df_mt5 = load_and_align_data(selected_pair, selected_cot_name, num_bars)

         if not df_merged.empty and 'Net_Pct_of_OI' in df_merged.columns:
             if oi_display_mode == "Overlay":
                 fig = build_overlay_chart(df_merged, selected_pair, selected_cot_name, date_density)
             elif oi_display_mode == "Heatmap Analysis":
                 fig = build_heatmap_chart(df_merged, selected_pair, selected_cot_name)
             else:
                 fig = build_stacked_chart(df_merged, selected_pair, selected_cot_name, date_density)
                 if enable_crosshair_oi:
                     fig = apply_shared_crosshair(fig)

             st.plotly_chart(fig, use_container_width=True)

             # Show a quick metric for latest OI
             st.markdown("### Latest Snapshot")
             latest_date = df_merged["Date"].iloc[-1].strftime("%Y-%m-%d")
             latest_oi = df_merged["Net_Pct_of_OI"].iloc[-1]
             latest_dxy_oi = df_merged["Net_Pct_of_OI_dxy"].iloc[-1]
             latest_price = df_merged["close"].iloc[-1]

             st.write(f"**Aligned Date:** {latest_date}")
             col1, col2, col3 = st.columns(3)
             col1.metric(label=f"Current Price ({selected_pair})", value=f"{latest_price:.5f}")
             col2.metric(label=f"{selected_cot_name} Net OI", value=f"{latest_oi:.2f}%")
             col3.metric(label="USD INDEX Net OI", value=f"{latest_dxy_oi:.2f}%")

         else:
             st.error("Could not fetch Open Interest or MT5 data for the selected assets.")


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
