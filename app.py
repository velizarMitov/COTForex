import streamlit as st

# We import the plotting logic and dictionary from our main script
from main import plot_cot_with_dxy, COT_TO_MT5

# Define Streamlit page basic setup
st.set_page_config(
    page_title="COT & MT5 Forex Analysis",
    layout="wide",
    page_icon="📈"
)

st.title("Forex COT vs Price Analysis")
st.markdown("Compare MT5 Weekly Close Prices directly with specific currency COT **AND** the USD Index COT on a single timeline.")

# Create the sidebar for user inputs
st.sidebar.header("Settings")

# Reverse the COT_TO_MT5 dict so we lookup COT names from MT5 symbols
mt5_to_cot = {mt5_sym: cot_name for cot_name, mt5_sym in COT_TO_MT5.items()}
mt5_options = list(mt5_to_cot.keys())

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

    # Render the new 3-subplot unified chart
    fig = plot_cot_with_dxy(selected_cot_name, num_bars=num_bars, height=1000)

    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Failed to generate the chart. Please check terminal logs for details.")

st.sidebar.markdown("---")
st.sidebar.info("Data sourced directly from **CFTC.gov** via Socrata API and local **MetaTrader 5** terminal.")
