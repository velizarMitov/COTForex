# COT & Forex Interactive Visualizer \U0001f4c8

A powerful Python-based analytics tool that automatically extracts data from two vital sources to create an interactive web interface for Forex trading analysis:
1. **CFTC Commitments of Traders (COT)** reports via the official Socrata API (`TFF - Futures Only` reporting for Net Speculative Positions).
2. **MetaTrader 5 (MT5)** local terminal connection (retrieving precise historical weekly OHLC prices).

By aligning these sets of data onto securely synced, dynamic timeline charts, the app allows technical and fundamental traders to directly compare institutional market sentiment with spot Forex movements.

---

## ⚡ Features
* **Live Integration:** Connects directly to any MT5 terminal and pulls real-time historical data.
* **Streamlit Web UI:** Three pages: Main Dashboard, Extremes & Comparison, and Open Interest Analysis.
* **Four chart views** of MT5 weekly close vs leveraged-funds Net % of Open Interest (pair and USD Index):
  - **Comparison (Aligned):** price with crowded-positioning markers, both OI panels on one shared scale (USD Index optionally inverted), the pair − USD spread, and a rolling price/OI correlation.
  - **Stacked:** price plus two OI panels (filled green/red areas), with an optional shared crosshair.
  - **Overlay:** price and both OI series on one panel.
  - **Heatmap:** correlation matrix plus month × year seasonality of OI and price.
* **Crowded positioning, defined once:** a week is "crowded" only when positioning is both **stretched versus the last year** (52-week percentile at or beyond the sidebar threshold) **and rare versus history** (Net % of OI beyond the P10/P90 of the data known at that week, so there is no look-ahead). Markers, the dashed zone lines, the Main page alerts and the Extremes warnings all use this rule. Expect roughly 10-15 markers per market over 20 years, and nothing before mid-2009 (the zones need 156 weeks of history).
* **USD-aware markers:** for USD-base pairs (`USDJPY`, `USDCHF`, `USDCAD`) the crowded-positioning markers point the way the *pair* is expected to move. Prices themselves are not inverted.
* **Caching:** CFTC data is cached for 6 hours and MT5 prices for 15 minutes, so changing chart options does not refetch. To force a refresh, choose **Clear cache** in Streamlit's top-right menu (or press `C`).
* **Gold (XAUUSD):** gold positioning comes from the CFTC *Disaggregated Futures Only* report (COMEX gold, **Managed Money**), while currencies use the *TFF* report (**Leveraged Funds**). The two categories are different populations, so gold's levels are not directly comparable with the currencies; the percentile, zones and crowded signal are relative to each market's own history. The MT5 symbol is detected automatically (`XAUUSD`, `GOLD`, suffixed names), so it works whatever your broker calls it.
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
4. Optional: install the ML stack (PyTorch) in a separate environment:
   ```powershell
   python -m pip install -r requirements-ml.txt
   ```

---

## 🖥️ Usage

Ensure your **MetaTrader 5** terminal is running in the background.
Double-click **`run_app.bat`**. It picks the virtual environment, installs missing dependencies, checks that MT5 is running, and opens the dashboard in your browser (served on `localhost` only). `run_app.bat ml` uses the `.venv-ml` environment instead.

Or, from your virtual environment inside the terminal, run:

```powershell
python -m streamlit run app.py
```

A tab will automatically open in your default browser at `http://localhost:8501`. 
* Use the **Sidebar** to toggle between Major Forex Pairs (EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, AUDUSD, NZDUSD) or Gold (XAUUSD).
* Adjust the slider to query more/fewer historical bars.
* Use Plotly's built-in toolbar to hover, zoom, or pan seamlessly across the MT5 price and the two CFTC subplots.

Quick preview without Streamlit (opens the Stacked chart in your browser):

```powershell
python main.py "EURO FX"
```

### Running tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests are offline and need neither network access nor a running MT5 terminal.

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

* `app.py` — Streamlit entry point: pages, sidebar controls, and the Extremes table.
* `data_processor.py` — Cached loading, COT↔MT5 date alignment, failure reporting, and the Extremes snapshot rows.
* `charts.py` — Plotly builders for the Comparison, Stacked, Overlay and Heatmap views.
* `ui_components.py` — Momentum metric tiles and sentiment-extreme panels.
* `cftc_api.py` — CFTC Socrata client and positioning metrics (Net % of OI, weekly change, 52-week percentile).
* `mt5_api.py` — MetaTrader 5 weekly price fetching.
* `symbols.py` — CFTC market ↔ MT5 symbol mapping and price precision per instrument.
* `main.py` — Command-line chart preview.
* `run_app.bat` — Single launcher (environment, dependency and MT5 checks, then starts the app).
* `tests/` — Offline `pytest` suite.
* `requirements.txt` — Core app dependencies only.
* `requirements-dev.txt` — Core dependencies plus `pytest`.
* `requirements-ml.txt` — Optional ML dependencies (`torch`) on top of core dependencies.

---

## \u26A0\uFE0F Notes
* CFTC Socrata endpoint updates once a week, so the timeframes map to `"W1"` (Weekly Bars) in MT5.
* If a Symbol is entirely missing, make sure it is added and fully loaded within MT5's "Market Watch" panel.
