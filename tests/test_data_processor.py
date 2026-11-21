import pandas as pd
import pytest

import data_processor
from cftc_api import calculate_extremes, calculate_momentum_metrics
from data_processor import load_and_align_data

REPORT_DATES = pd.date_range("2023-01-03", periods=60, freq="7D")  # Tuesdays


def _cot_frame(offset=0.0):
    df = pd.DataFrame({
        "Date": REPORT_DATES,
        "Net Position": [float(i) + offset for i in range(len(REPORT_DATES))],
        "Net_Pct_of_OI": [i / 10 + offset for i in range(len(REPORT_DATES))],
    })
    return calculate_extremes(calculate_momentum_metrics(df))


def _mt5_frame(start="2023-01-01"):
    idx = pd.date_range(start, periods=60, freq="7D", name="time")  # Sundays
    return pd.DataFrame({"close": [1.0 + i / 100 for i in range(60)]}, index=idx)


class _Calls:
    def __init__(self):
        self.cot = {}
        self.mt5 = 0


@pytest.fixture
def sources(monkeypatch):
    """Installs stub fetchers; returns a setter for which sources should fail."""
    calls = _Calls()
    state = {"empty": set(), "mt5_start": "2023-01-01"}

    def fake_cot(name):
        calls.cot[name] = calls.cot.get(name, 0) + 1
        return pd.DataFrame() if name in state["empty"] else _cot_frame()

    def fake_mt5(symbol, timeframe="W1", num_bars=1000):
        calls.mt5 += 1
        return pd.DataFrame() if "MT5" in state["empty"] else _mt5_frame(state["mt5_start"])

    monkeypatch.setattr(data_processor, "get_cot_data", fake_cot)
    monkeypatch.setattr(data_processor, "get_forex_data", fake_mt5)
    state["calls"] = calls
    return state


def test_success_has_no_error(sources):
    result = load_and_align_data("EURUSD", "EURO FX", 100)
    assert result.error is None
    assert not result.merged.empty
    assert {"close", "Net_Pct_of_OI", "Net_Pct_of_OI_dxy"} <= set(result.merged.columns)


def test_successful_loads_are_cached(sources):
    load_and_align_data("EURUSD", "EURO FX", 100)
    load_and_align_data("EURUSD", "EURO FX", 100)
    calls = sources["calls"]
    assert calls.cot == {"EURO FX": 1, "USD INDEX": 1}
    assert calls.mt5 == 1


def test_failed_loads_are_not_cached(sources):
    sources["empty"].add("EURO FX")
    load_and_align_data("EURUSD", "EURO FX", 100)
    load_and_align_data("EURUSD", "EURO FX", 100)
    assert sources["calls"].cot["EURO FX"] == 2


def test_cached_frames_are_not_shared(sources):
    first = load_and_align_data("EURUSD", "EURO FX", 100)
    first.cot["Net Position"] = -1
    second = load_and_align_data("EURUSD", "EURO FX", 100)
    assert (second.cot["Net Position"] != -1).any()


@pytest.mark.parametrize("failing, message", [
    ("EURO FX", "COT data for EURO FX unavailable"),
    ("USD INDEX", "USD Index COT data unavailable"),
    ("MT5", "MT5 price data for EURUSD unavailable (is the terminal running and logged in?)"),
])
def test_error_names_failed_source(sources, failing, message):
    sources["empty"].add(failing)
    result = load_and_align_data("EURUSD", "EURO FX", 100)
    assert result.error == message
    assert result.merged.empty


def test_error_when_dates_do_not_overlap(sources):
    sources["mt5_start"] = "2010-01-03"
    result = load_and_align_data("EURUSD", "EURO FX", 100)
    assert result.error == "No overlapping dates between COT and MT5 data"
