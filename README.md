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
