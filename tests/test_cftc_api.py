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


# --- crowded signal (confluence of rolling stretch and historical rarity) ---
from cftc_api import ZONE_WARMUP_WEEKS, calculate_crowded, crowded_masks, expanding_zone


def _oi_frame(oi, pct):
    return pd.DataFrame({
        "Date": pd.date_range("2000-01-04", periods=len(oi), freq="7D"),
        "Net_Pct_of_OI": np.asarray(oi, dtype=float),
        "52-Week Percentile": np.asarray(pct, dtype=float),
    })


def test_zone_has_no_values_during_warmup():
    lo, hi = expanding_zone(pd.Series(np.arange(300.0)))
    assert lo.iloc[: ZONE_WARMUP_WEEKS - 1].isna().all()
    assert hi.iloc[: ZONE_WARMUP_WEEKS - 1].isna().all()
    assert not np.isnan(hi.iloc[ZONE_WARMUP_WEEKS - 1])


def test_zone_ignores_later_data():
    series = pd.Series(np.sin(np.arange(400) / 7.0) * 20)
    lo_full, hi_full = expanding_zone(series)
    lo_cut, hi_cut = expanding_zone(series.iloc[:250])
    pd.testing.assert_series_equal(lo_full.iloc[:250], lo_cut)
    pd.testing.assert_series_equal(hi_full.iloc[:250], hi_cut)


def test_signal_is_zero_during_warmup():
    df = calculate_crowded(_oi_frame(np.arange(100.0), np.full(100, 100.0)))
    assert (df["Crowded Signal"] == 0).all()


def test_confluence_scenarios():
    n = 300
    oi = np.zeros(n)
    oi[:-3] = np.sin(np.arange(n - 3) / 5.0) * 10
    oi[-3:] = [50.0, 0.0, 50.0]
    pct = np.full(n, 50.0)
    pct[-3:] = [100.0, 100.0, 40.0]
    df = calculate_crowded(_oi_frame(oi, pct))

    assert list(df["Crowded Signal"].iloc[-3:]) == [1, 0, 0]


def test_crowded_short_needs_both_sides():
    n = 300
    oi = np.sin(np.arange(n) / 5.0) * 10
    oi[-1] = -50.0
    pct = np.full(n, 50.0)
    pct[-1] = 0.0
    df = calculate_crowded(_oi_frame(oi, pct))
    assert df["Crowded Signal"].iloc[-1] == -1


def test_crowded_masks_respect_threshold():
    long_, short = crowded_masks([95, 85, 5], [30, 30, -30], [-10] * 3, [10] * 3, threshold=90)
    assert list(long_) == [True, False, False]
    assert list(short) == [False, False, True]
    long_95, _ = crowded_masks([92], [30], [-10], [10], threshold=95)
    assert not long_95[0]
