# COT & Forex Interactive Visualizer \U0001f4c8

A powerful Python-based analytics tool that automatically extracts data from two vital sources to create an interactive web interface for Forex trading analysis:
1. **CFTC Commitments of Traders (COT)** reports via the official Socrata API (`TFF - Futures Only` reporting for Net Speculative Positions).
2. **MetaTrader 5 (MT5)** local terminal connection (retrieving precise historical weekly OHLC prices).

By aligning these sets of data onto securely synced, dynamic timeline charts, the app allows technical and fundamental traders to directly compare institutional market sentiment with spot Forex movements.

---

## ⚡ Features
* **Live Integration:** Connects directly to any MT5 terminal and pulls real-time historical data.
* **Auto-Inversion:** Automatically inverses prices for counter-USD bases (like `USDJPY` or `USDCHF`) to accurately reflect standard COT futures contracts.
* **Streamlit Web UI:** Leverages a lightweight Streamlit web application.
* **Triple-Axis Correlation Visuals:** Renders three synchronous Plotly charts:
  - **MT5 Close Price** (Line Chart)
  - **Selected Pair Net COT Position** (Bar Chart; Green/Red for divergence spotting)
  - **U.S. DOLLAR INDEX (DXY) COT Position** (Bar Chart; overlaying general USD strength)
* **Zero Maintenance Mapping:** Uses smart mappings (`EURO FX` -> `EURUSD`) to abstract away complex labeling.

---

## 🔧 Prerequisites

You must have:
* **Python 3.9+** (Supports up to 3.13)
* **MetaTrader 5 Client:** Must be installed, open, and successfully connected to a broker on a Windows machine.

---

## 🚀 Installation & Setup

1. Clone this repository or move the source files into a dedicated workspace.
2. Initialize your `.venv` virtual environment (or use your existing setup).
3. Install core app dependencies (lightweight):
   ```powershell
   python -m pip install -r requirements.txt
   ```
   *(Includes `pandas`, `MetaTrader5`, `plotly`, and `streamlit`.)*
4. Optional: install ML stack (PyTorch + TensorFlow) in a separate environment:
   ```powershell
   python -m pip install -r requirements-ml.txt
   ```

---

## 🖥️ Usage

Ensure your **MetaTrader 5** terminal is running in the background.
From your virtual environment inside the terminal, simply run:

```powershell
python -m streamlit run app.py
```

A tab will automatically open in your default browser at `http://localhost:8501`. 
* Use the **Sidebar** to toggle between Major Forex Pairs (EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, AUDUSD, NZDUSD).
* Adjust the slider to query more/fewer historical bars.
* Use Plotly's built-in toolbar to hover, zoom, or pan seamlessly across the MT5 price and the two CFTC subplots.

---

### Data Selection Rationale: Why These Specific Indicators?

To adhere to the Scientific Method and ensure our exploratory and statistical analysis is robust, every variable extracted was deliberately chosen to represent a specific facet of the macroeconomic machine. Furthermore, understanding the distinct statistical characteristics and reporting frequencies of these variables is crucial for our data handling strategy.

*   **S&P 500 (`^GSPC`)**: Serves as our primary dependent variable. It is the ultimate benchmark for US equity market performance, reflecting aggregate corporate earnings expectations and overall investor risk appetite. 
    *   *Data Characteristics*: High-frequency (daily) continuous numerical time-series. Because absolute equity prices exhibit non-stationary, exponential upward trends, this data will require mathematical transformation into percentage changes (returns) to be viable for statistical testing.
*   **10-Year and 2-Year Treasury Yields (`DGS10` & `DGS2`)**: These are the core independent variables of our study. The mathematical difference (spread) between the long-term (10Y) and short-term (2Y) borrowing costs is universally recognized as the most reliable leading indicator of impending recessions. 
    *   *Data Characteristics*: High-frequency (daily) continuous numerical data. These variables are highly cyclical and will be used to engineer a new categorical feature: the 'Yield Curve State' (Normal vs. Inverted).
*   **Consumer Price Index (`CPIAUCSL`)**: Essential for advanced exploratory data analysis. Inflation acts as a hidden mediating factor in financial markets. By tracking CPI, we can segment our timeline into distinct economic regimes (e.g., 'High Inflation' vs. 'Low Inflation').
    *   *Data Characteristics*: Lower-frequency (monthly) continuous data.
*   **Gross Domestic Product (`GDP`) & US Dollar Index (`DX-Y.NYB`)**: These provide critical macroeconomic context. GDP serves as the ultimate scorecard for absolute economic output, while the US Dollar Index reflects global liquidity and currency strength.
    *   *Data Characteristics*: GDP is a low-frequency (quarterly) lagging indicator, while the DXY is a high-frequency (daily) concurrent indicator. 

**Methodological Implication:** 
By consolidating these specific features, we construct a multi-dimensional dataset perfectly tailored to test our hypothesis. However, the inherent heterogeneity in their reporting frequencies (daily vs. monthly vs. quarterly) explicitly dictates our Data Tidying approach: we must employ forward-filling (`ffill()`) techniques to align the macroeconomic data with the daily trading calendar without introducing look-ahead bias.

---

## 📂 Project Structure

* `main.py` — Core data merger and robust Plotly chart generation.
* `app.py` — The Streamlit entry point; wraps the charts into the clean web UI elements.
* `mt5_api.py` — Interactor class logic managing MetaTrader 5 fetching and normalization.
* `cftc_api.py` — Socrata/CFTC API endpoints handler, parsing JSON records into pandas DataFrames.
* `requirements.txt` — Core app dependencies only.
* `requirements-ml.txt` — Optional ML dependencies (`torch`, `tensorflow`) on top of core dependencies.

---

## \u26A0\uFE0F Notes
* CFTC Socrata endpoint updates once a week, so the timeframes map to `"W1"` (Weekly Bars) in MT5.
* If a Symbol is entirely missing, make sure it is added and fully loaded within MT5's "Market Watch" panel.
