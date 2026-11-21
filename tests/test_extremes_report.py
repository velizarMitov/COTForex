import io

import numpy as np
import pandas as pd

import data_processor
from app import crowded_assets
from cftc_api import calculate_extremes
from data_processor import _extreme_row, get_comparison_data


def _cot(values):
    df = pd.DataFrame({
        "Date": pd.date_range("2023-01-03", periods=len(values), freq="7D"),
        "Net Position": values,
    })
    return calculate_extremes(df)


def test_pair_and_usd_rows_share_columns(monkeypatch):
    monkeypatch.setattr(data_processor, "get_cot_data", lambda _n: _cot(np.arange(60.0)))
    res = get_comparison_data(["EURUSD", "USDJPY"], include_usd=True)

    assert list(res["Asset"]) == ["EURUSD (EURO FX)", "USDJPY (JAPANESE YEN)", "DXY (USD INDEX)"]
    assert res.notna().all().all()


def test_row_min_max_match_percentile_window():
    row = _extreme_row("X", _cot(list(np.arange(60.0)) + [100.0]))
    assert row["Current Net Pos"] == row["52W Max"] == 100
    assert row["52W Percentile (%)"] == 100


def test_missing_values_become_none():
    df = _cot(np.arange(60.0))
    df.loc[df.index[-1], ["52-Week Percentile", "52W Min"]] = np.nan
    row = _extreme_row("X", df)
    assert row["52W Percentile (%)"] is None
    assert row["52W Min"] is None


def test_missing_percentile_raises_no_warning_and_exports_blank():
    res = pd.DataFrame([
        {"Asset": "A", "52W Percentile (%)": 95.0},
        {"Asset": "B", "52W Percentile (%)": None},
        {"Asset": "C", "52W Percentile (%)": 5.0},
    ])
    bull, bear = crowded_assets(res)
    assert list(bull["Asset"]) == ["A"]
    assert list(bear["Asset"]) == ["C"]

    exported = pd.read_csv(io.StringIO(res.to_csv(index=False)), keep_default_na=False)
    assert exported.loc[1, "52W Percentile (%)"] == ""
    assert list(exported.columns) == list(res.columns)


def test_no_extremes_when_all_within_bounds():
    bull, bear = crowded_assets(pd.DataFrame({"Asset": ["A"], "52W Percentile (%)": [50.0]}))
    assert bull.empty and bear.empty
