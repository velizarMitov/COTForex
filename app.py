import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# We import the plotting logic and dictionary from our main script
from main import plot_cot_with_dxy, COT_TO_MT5
from cftc_api import get_cot_data
from mt5_api import get_forex_data

# Reverse the COT_TO_MT5 dict so we lookup COT names from MT5 symbols
mt5_to_cot = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}
mt5_options = list(mt5_to_cot.keys())


def _build_overlay_chart(df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = ["#16a34a" if val > 0 else "#dc2626" for val in df_merged["Net_Pct_of_OI"]]

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color="gold", width=2.5),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>MT5 Price=%{y:.5f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI"],
            name=f"{selected_cot_name} Net OI %",
            marker_color=colors,
            opacity=0.4,
            hovertemplate="Date=%{x|%Y-%m-%d}<br>Pair Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI_dxy"],
            mode="lines+markers",
            name="USD Index Net OI %",
            line=dict(color="dodgerblue", width=2),
            marker=dict(size=4),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>USD Index Net OI=%{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="gray", secondary_y=True)
    fig.update_layout(
        title=f"<b>{selected_pair} Price vs Net OI% (Overlay)</b>",
        xaxis_title="Date",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=760,
    )
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(title_text="Net Open Interest (%)", secondary_y=True)

    if selected_pair in ["USDJPY", "USDCHF", "USDCAD"]:
        fig.update_yaxes(autorange="reversed", secondary_y=False)
        fig.update_yaxes(title_text="Price (Inverted Axis)", secondary_y=False)

    return fig


def _build_stacked_chart(df_merged: pd.DataFrame, selected_pair: str, selected_cot_name: str) -> go.Figure:
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            f"{selected_pair} MT5 Price",
            f"{selected_cot_name} Net OI %",
            "USD INDEX Net OI %",
        ),
    )

    colors = ["#16a34a" if val > 0 else "#dc2626" for val in df_merged["Net_Pct_of_OI"]]

    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["close"],
            mode="lines",
            name="MT5 Price",
            line=dict(color="gold", width=2.5),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>MT5 Price=%{y:.5f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI"],
            name=f"{selected_cot_name} Net OI %",
            marker_color=colors,
            opacity=0.5,
            hovertemplate="Date=%{x|%Y-%m-%d}<br>Pair Net OI=%{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_merged["Date"],
            y=df_merged["Net_Pct_of_OI_dxy"],
            mode="lines+markers",
            name="USD Index Net OI %",
            line=dict(color="dodgerblue", width=2),
            marker=dict(size=4),
            hovertemplate="Date=%{x|%Y-%m-%d}<br>USD Index Net OI=%{y:.2f}%<extra></extra>",
        ),
        row=3,
        col=1,
    )

    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=3, col=1)
    fig.update_layout(
        title=f"<b>{selected_pair} Price and OI% (Stacked)</b>",
        hovermode="x unified",
        height=980,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Pair Net OI %", row=2, col=1)
    fig.update_yaxes(title_text="USD Index Net OI %", row=3, col=1)

    if selected_pair in ["USDJPY", "USDCHF", "USDCAD"]:
        fig.update_yaxes(autorange="reversed", row=1, col=1)
        fig.update_yaxes(title_text="Price (Inverted Axis)", row=1, col=1)

    return fig


def render_main_dashboard():
    st.title("Forex COT vs Price Analysis")
    st.markdown("Compare MT5 Weekly Close Prices directly with specific currency COT **AND** the USD Index COT on a single timeline.")

    # Create the sidebar for user inputs
    st.sidebar.header("Settings")

    selected_pair = st.sidebar.selectbox("Select Currency Pair", mt5_options)
    display_mode = st.sidebar.radio(
        "Chart View",
        ["Stacked (one under another)", "Overlay"],
        index=0,
        help="Stacked = easier reading, Overlay = direct correlation view",
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
        df_cot = get_cot_data(selected_cot_name)
        df_dxy = get_cot_data('USD INDEX')
        df_mt5 = get_forex_data(selected_pair, timeframe="W1", num_bars=num_bars)

        if not df_cot.empty and not df_mt5.empty and not df_dxy.empty:
            # Safely cast dates
            df_cot['Date'] = pd.to_datetime(df_cot['Date']).dt.tz_localize(None)
            df_dxy['Date'] = pd.to_datetime(df_dxy['Date']).dt.tz_localize(None)

            # Align COT and DXY exactly
            df_cot_merged = pd.merge(
                df_cot[['Date', 'Net Position', 'Net_Pct_of_OI']],
                df_dxy[['Date', 'Net Position', 'Net_Pct_of_OI']],
                on='Date', how='inner', suffixes=('', '_dxy')
            ).sort_values('Date')

            # Align MT5 data
            df_mt5_reset = df_mt5.reset_index()
            if 'time' in df_mt5_reset.columns:
                df_mt5_reset = df_mt5_reset.rename(columns={'time': 'Date'})
            df_mt5_reset['Date'] = pd.to_datetime(df_mt5_reset['Date']).dt.tz_localize(None)

            # Force identical resolution to prevent MergeError
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
                st.error("No overlapping dates found.")
                return

            if display_mode == "Overlay":
                fig = _build_overlay_chart(df_merged, selected_pair, selected_cot_name)
            else:
                fig = _build_stacked_chart(df_merged, selected_pair, selected_cot_name)

            st.subheader("Weekly Momentum Metrics")
            col1, col2, col3 = st.columns(3)

            # Calculate & Display MT5 Metrics
            if len(df_mt5) >= 2:
                current_price = df_mt5['close'].iloc[-1]
                prev_price = df_mt5['close'].iloc[-2]
                price_change = current_price - prev_price
                price_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
                col1.metric(
                    label=f"{selected_pair} Weekly Close",
                    value=f"{current_price:.5f}",
                    delta=f"{price_change:+.5f} ({price_pct:+.2f}%)"
                )

            # Calculate & Display COT Metrics
            if not df_cot.empty:
                current_cot = df_cot['Net Position'].iloc[-1]
                cot_change = df_cot['Net Position Change'].iloc[-1]
                cot_pct = df_cot['Net Position % Change'].iloc[-1]
                col2.metric(
                    label=f"{selected_cot_name} Net Pos",
                    value=f"{int(current_cot):,}",
                    delta=f"{int(cot_change):+,} ({cot_pct:+.2f}%)"
                )

            # Calculate & Display DXY Metrics
            if not df_dxy.empty:
                current_dxy = df_dxy['Net Position'].iloc[-1]
                dxy_change = df_dxy['Net Position Change'].iloc[-1]
                dxy_pct = df_dxy['Net Position % Change'].iloc[-1]
                col3.metric(
                    label="USD INDEX Net Pos",
                    value=f"{int(current_dxy):,}",
                    delta=f"{int(dxy_change):+,} ({dxy_pct:+.2f}%)"
                )

            st.markdown("---")

            st.subheader("Market Sentiment Extremes")
            ext1, ext2 = st.columns(2)

            def check_extremes(col_obj, name, cot_index):
                col_obj.write(f"**{name} 52-Week Percentile**: {cot_index:.1f}%")
                if cot_index >= 90:
                    col_obj.error("Extreme Bullish Sentiment (>=90%) - Potential Crowded Long (Reversal Zone)")
                elif cot_index <= 10:
                    col_obj.error("Extreme Bearish Sentiment (<=10%) - Potential Crowded Short (Reversal Zone)")
                else:
                    col_obj.success("Neutral sentiment bounds within normal range.")

            if not df_cot.empty:
                check_extremes(ext1, selected_cot_name, df_cot['52-Week Percentile'].iloc[-1])

            if not df_dxy.empty:
                check_extremes(ext2, "USD INDEX", df_dxy['52-Week Percentile'].iloc[-1])

            st.markdown("---")

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to generate the chart. Please check terminal logs for details.")


def render_extremes_comparison():
    st.title("Market Sentiment Extremes & Comparison")
    st.markdown("Compare 52-Week Percentiles across multiple selected Forex pairs and the USD Index.")
    
    st.sidebar.header("Comparison Settings")
    # Default select first 3 pairs + we manually add USD INDEX below
    selected_pairs_mt5 = st.sidebar.multiselect("Select Forex Pairs", mt5_options, default=mt5_options[:3])
    include_usd = st.sidebar.checkbox("Include USD INDEX", value=True)
    
    if selected_pairs_mt5 or include_usd:
        with st.spinner("Fetching comparison data..."):
            results = []
            
            # 1. Fetch selected FX pairs
            for mt5_sym in selected_pairs_mt5:
                cot_name = mt5_to_cot[mt5_sym]
                df = get_cot_data(cot_name)
                if not df.empty:
                    latest = df.iloc[-1]
                    
                    # Manual 52-week calculation just to ensure exact prompt logic for safety
                    roll_min_52 = df["Net Position"].rolling(window=52, min_periods=1).min().iloc[-1]
                    roll_max_52 = df["Net Position"].rolling(window=52, min_periods=1).max().iloc[-1]
                    
                    results.append({
                        "Asset": mt5_sym + f" ({cot_name})",
                        "Date": latest["Date"].strftime("%Y-%m-%d"),
                        "Current Net Pos": int(latest["Net Position"]),
                        "52W Min": int(roll_min_52),
                        "52W Max": int(roll_max_52),
                        "52W Percentile (%)": round(latest["52-Week Percentile"], 2)
                    })
                    
            # 2. Fetch USD Index
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
            
            if results:
                res_df = pd.DataFrame(results)
                
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
        ["Stacked (one under another)", "Overlay"],
        index=0,
        key="oi_chart_view",
        help="Stacked = clearer read, Overlay = compare on one panel",
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
        df_cot = get_cot_data(selected_cot_name)
        df_dxy = get_cot_data('USD INDEX')
        df_mt5 = get_forex_data(selected_pair, timeframe="W1", num_bars=num_bars)
        
        if not df_cot.empty and 'Net_Pct_of_OI' in df_cot.columns and not df_mt5.empty and not df_dxy.empty:
            # Safely cast dates
            df_cot['Date'] = pd.to_datetime(df_cot['Date']).dt.tz_localize(None)
            df_dxy['Date'] = pd.to_datetime(df_dxy['Date']).dt.tz_localize(None)
            
            # 1. Align COT and DXY exactly
            df_cot_merged = pd.merge(
                df_cot[['Date', 'Net_Pct_of_OI']], 
                df_dxy[['Date', 'Net_Pct_of_OI']], 
                on='Date', how='inner', suffixes=('', '_dxy')
            ).sort_values('Date')
            
            # 2. Align MT5 data using merge_asof
            df_mt5_reset = df_mt5.reset_index()
            if 'time' in df_mt5_reset.columns:
                df_mt5_reset = df_mt5_reset.rename(columns={'time': 'Date'})
            df_mt5_reset['Date'] = pd.to_datetime(df_mt5_reset['Date']).dt.tz_localize(None)
            
            # Force identical resolution to prevent MergeError
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
                st.error("No overlapping dates found after aligning MT5 and COT data.")
                return

            if oi_display_mode == "Overlay":
                fig = _build_overlay_chart(df_merged, selected_pair, selected_cot_name)
            else:
                fig = _build_stacked_chart(df_merged, selected_pair, selected_cot_name)

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
