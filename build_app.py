import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# We import the plotting logic and dictionary from our main script
from main import plot_cot_with_dxy, COT_TO_MT5
from cftc_api import get_cot_data

# Define Streamlit page basic setup
st.set_page_config(
    page_title="COT & MT5 Forex Analysis",
    layout="wide",
    page_icon="📈"
)

# Navigation via sidebar
page = st.sidebar.radio('Navigation', ['Main Dashboard', 'Extremes & Comparison', 'Open Interest Analysis'])
st.sidebar.markdown("---")

# Reverse the COT_TO_MT5 dict so we lookup COT names from MT5 symbols
mt5_to_cot = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}
mt5_options = list(mt5_to_cot.keys())

if page == 'Main Dashboard':
    st.title("Forex COT vs Price Analysis")
    st.markdown("Compare MT5 Weekly Close Prices directly with specific currency COT **AND** the USD Index COT on a single timeline.")

    # Create the sidebar for user inputs
    st.sidebar.header("Settings")

    selected_pair = st.sidebar.selectbox("Select Currency Pair", mt5_options)

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

        # Render the new 3-subplot unified chart and get raw dataframes
        res = plot_cot_with_dxy(selected_cot_name, num_bars=num_bars, height=1000)

        if res is not None:
            fig, df_mt5, df_cot, df_dxy_cot = res

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
            if not df_dxy_cot.empty:
                current_dxy = df_dxy_cot['Net Position'].iloc[-1]
                dxy_change = df_dxy_cot['Net Position Change'].iloc[-1]
                dxy_pct = df_dxy_cot['Net Position % Change'].iloc[-1]
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
                    col_obj.error("🚨 **Extreme Bullish Sentiment** (>=90%) - Potential Crowded Long (Reversal Zone)")
                elif cot_index <= 10:
                    col_obj.error("🚨 **Extreme Bearish Sentiment** (<=10%) - Potential Crowded Short (Reversal Zone)")
                else:
                    col_obj.success("✅ **Neutral Sentiment** bounds within normal range.")

            if not df_cot.empty:
                check_extremes(ext1, selected_cot_name, df_cot['52-Week Percentile'].iloc[-1])
            
            if not df_dxy_cot.empty:
                check_extremes(ext2, "USD INDEX", df_dxy_cot['52-Week Percentile'].iloc[-1])

            st.markdown("---")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to generate the chart. Please check terminal logs for details.")

elif page == 'Extremes & Comparison':
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
                styled_df = res_df.style.applymap(highlight_percentile, subset=["52W Percentile (%)"])
                
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

elif page == 'Open Interest Analysis':
    st.title("Open Interest Analysis")
    st.markdown("Analyze the net percentage of Open Interest (OI) held by leveraged speculative funds.")
    
    st.sidebar.header("OI Settings")
    selected_pair = st.sidebar.selectbox("Select Currency Pair", mt5_options)
    selected_cot_name = mt5_to_cot[selected_pair]
    
    with st.spinner("Fetching Open Interest data..."):
        df_cot = get_cot_data(selected_cot_name)
        
        if not df_cot.empty and 'Net_Pct_of_OI' in df_cot.columns:
            fig = go.Figure()
            
            # Add line for Net_Pct_of_OI
            fig.add_trace(go.Scatter(
                x=df_cot["Date"],
                y=df_cot["Net_Pct_of_OI"],
                mode='lines',
                name='Net Pct of OI',
                line=dict(color='purple', width=2)
            ))
            
            # Add a horizontal line at 0 for crossing signals
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Zero Line (Long/Short Flip)", annotation_position="bottom right")
            
            fig.update_layout(
                title=f"<b>Net Speculative Open Interest (%) for {selected_cot_name}</b>",
                xaxis_title="Date",
                yaxis_title="Net Open Interest (%)",
                hovermode="x unified",
                template="plotly_white",
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show a quick metric for latest OI
            st.markdown("### Latest OI Snapshot")
            latest_oi = df_cot["Net_Pct_of_OI"].iloc[-1]
            st.metric(label=f"Current Net Speculative OI ({selected_cot_name})", value=f"{latest_oi:.2f}%")
            
        else:
            st.error("Could not fetch Open Interest data for the selected asset.")

st.sidebar.markdown("---")
st.sidebar.info("Data sourced directly from **CFTC.gov** via Socrata API and local **MetaTrader 5** terminal.")

