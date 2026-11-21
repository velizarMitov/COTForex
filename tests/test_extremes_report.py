import io

import numpy as np
import pandas as pd

import data_processor
from app import crowded_assets
from cftc_api import calculate_crowded, calculate_extremes, crowded_verdict
from data_processor import _extreme_row, get_comparison_data


def _cot(values, oi=None):
    n = len(values)
    df = pd.DataFrame({
        "Date": pd.date_range("2018-01-02", periods=n, freq="7D"),
        "Net Position": np.asarray(values, dtype=float),
        "Net_Pct_of_OI": np.asarray(values if oi is None else oi, dtype=float) / 10,
    })
    return calculate_crowded(calculate_extremes(df))


def _wave(n=260):
    return list(np.sin(np.arange(n) / 6.0) * 1000)


def test_pair_and_usd_rows_share_columns(monkeypatch):
    monkeypatch.setattr(data_processor, "get_cot_data", lambda _n: _cot(_wave()))
    res = get_comparison_data(["EURUSD", "USDJPY"], include_usd=True)

    assert list(res["Asset"]) == ["EURUSD (EURO FX)", "USDJPY (JAPANESE YEN)", "DXY (USD INDEX)"]
    assert res.notna().all().all()


def test_row_min_max_match_percentile_window():
    row = _extreme_row("X", _cot(_wave() + [5000.0]))
    assert row["Current Net Pos"] == row["52W Max"] == 5000
    assert row["52W Percentile (%)"] == 100


def test_missing_values_become_none():
    df = _cot(_wave())
    df.loc[df.index[-1], ["52-Week Percentile", "52W Min"]] = np.nan
    row = _extreme_row("X", df)
    assert row["52W Percentile (%)"] is None
    assert row["52W Min"] is None


def test_latest_week_crowded_long():
    row = _extreme_row("X", _cot(_wave() + [5000.0]))
    assert row["Crowded"] == "Long"


def test_latest_week_crowded_short():
    row = _extreme_row("X", _cot(_wave() + [-5000.0]))
    assert row["Crowded"] == "Short"


def test_stretched_but_inside_history_is_not_crowded():
    # Net Position pinned at its 52w high (percentile 100) while Net OI stays mid-range.
    values = _wave() + [900.0]
    oi = _wave() + [0.0]
    df = _cot(values, oi)
    assert df["52-Week Percentile"].iloc[-1] > 90
    assert _extreme_row("X", df)["Crowded"] == "No"


def test_short_history_reports_insufficient():
    row = _extreme_row("X", _cot(_wave(100)))
    assert row["Crowded"] == "Insufficient history"
    assert crowded_verdict(_cot(_wave(100)).iloc[-1]) == "warmup"


def test_missing_percentile_raises_no_warning_and_exports_blank():
    res = pd.DataFrame([
        {"Asset": "A", "52W Percentile (%)": 95.0, "Crowded": "Long"},
        {"Asset": "B", "52W Percentile (%)": None, "Crowded": "Insufficient history"},
        {"Asset": "C", "52W Percentile (%)": 5.0, "Crowded": "Short"},
        {"Asset": "D", "52W Percentile (%)": 100.0, "Crowded": "No"},
    ])
    bull, bear = crowded_assets(res)
    assert list(bull["Asset"]) == ["A"]
    assert list(bear["Asset"]) == ["C"]

    exported = pd.read_csv(io.StringIO(res.to_csv(index=False)), keep_default_na=False)
    assert exported.loc[1, "52W Percentile (%)"] == ""
    assert list(exported.columns) == list(res.columns)


def test_no_extremes_when_nothing_is_crowded():
    bull, bear = crowded_assets(pd.DataFrame({"Asset": ["A"], "Crowded": ["No"]}))
    assert bull.empty and bear.empty
