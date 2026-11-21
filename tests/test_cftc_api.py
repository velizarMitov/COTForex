import numpy as np
import pandas as pd
import pytest

import cftc_api
from cftc_api import calculate_extremes, calculate_momentum_metrics, get_cot_data


def _row(date, long_, short, pct_long, pct_short):
    return {
        "report_date_as_yyyy_mm_dd": date,
        "lev_money_positions_long": str(long_),
        "lev_money_positions_short": str(short),
        "pct_of_oi_lev_money_long": str(pct_long),
        "pct_of_oi_lev_money_short": str(pct_short),
    }


@pytest.fixture
def stub_rows(monkeypatch):
    def _install(rows):
        monkeypatch.setattr(cftc_api, "_fetch_rows", lambda _name: rows)
    return _install


def _assert_rows_aligned(df):
    expected = (
        pd.to_numeric(df["pct_of_oi_lev_money_long"])
        - pd.to_numeric(df["pct_of_oi_lev_money_short"])
    )
    np.testing.assert_allclose(df["Net_Pct_of_OI"], expected)


def test_unsorted_rows_are_sorted_and_stay_aligned(stub_rows):
    stub_rows([
        _row("2024-01-16T00:00:00.000", 300, 100, 30.0, 10.0),
        _row("2024-01-02T00:00:00.000", 100, 50, 11.0, 5.0),
        _row("2024-01-09T00:00:00.000", 200, 80, 22.0, 8.0),
    ])
    df = get_cot_data("EURO FX")

    assert list(df["Date"].dt.strftime("%Y-%m-%d")) == ["2024-01-02", "2024-01-09", "2024-01-16"]
    assert list(df["Net Position"]) == [50, 120, 200]
    assert list(df["Net_Pct_of_OI"]) == [6.0, 14.0, 20.0]
    _assert_rows_aligned(df)


def test_invalid_date_row_is_dropped_without_misalignment(stub_rows):
    stub_rows([
        _row("2024-01-02T00:00:00.000", 100, 50, 11.0, 5.0),
        _row("not-a-date", 999, 0, 99.0, 0.0),
        _row("2024-01-09T00:00:00.000", 200, 80, 22.0, 8.0),
        _row("2024-01-16T00:00:00.000", 300, 100, 30.0, 10.0),
    ])
    df = get_cot_data("EURO FX")

    assert len(df) == 3
    assert list(df["Net_Pct_of_OI"]) == [6.0, 14.0, 20.0]
    _assert_rows_aligned(df)


def test_fetch_failure_returns_empty_frame(monkeypatch):
    def _boom(_name):
        raise OSError("network down")
    monkeypatch.setattr(cftc_api, "_fetch_rows", _boom)
    assert get_cot_data("EURO FX").empty


def _weekly(values):
    return pd.DataFrame({
        "Date": pd.date_range("2020-01-07", periods=len(values), freq="7D"),
        "Net Position": values,
    })


def test_percentile_neutral_before_min_history():
    df = calculate_extremes(_weekly(np.arange(40, dtype=float)))
    assert (df["52-Week Percentile"].iloc[:25] == 50).all()
    assert df["52-Week Percentile"].iloc[25] == 100


def test_percentile_neutral_on_flat_range():
    df = calculate_extremes(_weekly([7.0] * 60))
    assert (df["52-Week Percentile"] == 50).all()


def test_latest_at_52w_max_is_percentile_100():
    values = list(np.sin(np.linspace(0, 12, 120)) * 1000) + [5000.0]
    df = calculate_extremes(_weekly(values))
    latest = df.iloc[-1]
    assert latest["Net Position"] == latest["52W Max"]
    assert latest["52-Week Percentile"] == 100


def test_min_max_use_percentile_window():
    df = calculate_extremes(_weekly(np.arange(40, dtype=float)))
    assert df["52W Min"].iloc[:25].isna().all()
    assert df["52W Min"].iloc[-1] == 0
    assert df["52W Max"].iloc[-1] == 39


def test_momentum_metrics_week_over_week():
    df = calculate_momentum_metrics(_weekly([100.0, 150.0, 0.0, 50.0]))
    assert list(df["Net Position Change"]) == [0, 50, -150, 50]
    assert list(df["Net Position % Change"]) == [0, 50, -100, 0]
