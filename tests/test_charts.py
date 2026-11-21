import numpy as np
import pandas as pd
import pytest

from cftc_api import ZONE_WARMUP_WEEKS, expanding_zone
from charts import NEG, POS, _rgba, apply_shared_crosshair, build_comparison_chart, build_stacked_chart

N = 220
CROWDED_WEEK = 190


def _merged(pct_at_extreme, oi_at_extreme):
    """Synthetic frame whose week CROWDED_WEEK..+3 has the given percentile and pair OI."""
    pct = np.full(N, 50.0)
    pct[CROWDED_WEEK:CROWDED_WEEK + 4] = pct_at_extreme
    oi = np.sin(np.linspace(0, 30, N)) * 10
    oi[CROWDED_WEEK:CROWDED_WEEK + 4] = oi_at_extreme
    dxy = np.cos(np.linspace(0, 30, N)) * 15
    df = pd.DataFrame({
        "Date": pd.date_range("2018-01-02", periods=N, freq="7D"),
        "close": np.linspace(1.0, 1.2, N),
        "Net_Pct_of_OI": oi,
        "Net_Pct_of_OI_dxy": dxy,
        "52-Week Percentile": pct,
    })
    df["OI Zone Lo"], df["OI Zone Hi"] = expanding_zone(df["Net_Pct_of_OI"])
    df["OI Zone Lo_dxy"], df["OI Zone Hi_dxy"] = expanding_zone(df["Net_Pct_of_OI_dxy"])
    return df


def _markers(fig, prefix):
    return [t for t in fig.data if t.name and t.name.startswith(prefix)]


def _marker(fig, prefix):
    traces = _markers(fig, prefix)
    assert len(traces) == 1, f"expected one '{prefix}' trace"
    return traces[0]


def _assert_marker(fig, df, prefix, symbol, color, above):
    trace = _marker(fig, prefix)
    assert trace.marker.symbol == symbol
    assert trace.marker.color == _rgba(color, 0.95)
    price = df["close"].iloc[CROWDED_WEEK]
    assert (trace.y[0] > price) if above else (trace.y[0] < price)


@pytest.mark.parametrize("pair, cot, pct, oi, prefix, symbol, color, above", [
    ("EURUSD", "EURO FX", 95, 60, "Crowded LONG", "triangle-down", NEG, True),
    ("EURUSD", "EURO FX", 5, -60, "Crowded SHORT", "triangle-up", POS, False),
    ("USDJPY", "JAPANESE YEN", 95, 60, "Crowded LONG", "triangle-up", POS, False),
    ("USDCHF", "SWISS FRANC", 5, -60, "Crowded SHORT", "triangle-down", NEG, True),
])
def test_marker_points_to_pair_unwind_direction(pair, cot, pct, oi, prefix, symbol, color, above):
    df = _merged(pct, oi)
    fig = build_comparison_chart(df, pair, cot)
    _assert_marker(fig, df, prefix, symbol, color, above)


def test_marker_label_names_futures_side():
    fig = build_comparison_chart(_merged(95, 60), "USDJPY", "JAPANESE YEN")
    assert _marker(fig, "Crowded LONG").name.startswith("Crowded LONG Japanese Yen futures")


def test_stretched_but_not_historically_rare_draws_no_marker():
    fig = build_comparison_chart(_merged(100, 0.0), "EURUSD", "EURO FX")
    assert not _markers(fig, "Crowded")


def test_historically_rare_but_not_stretched_draws_no_marker():
    fig = build_comparison_chart(_merged(60, 60), "EURUSD", "EURO FX")
    assert not _markers(fig, "Crowded")


def test_threshold_slider_only_moves_the_percentile_side():
    df = _merged(92, 60)
    assert _markers(build_comparison_chart(df, "EURUSD", "EURO FX", extreme_threshold=90), "Crowded LONG")
    assert not _markers(build_comparison_chart(df, "EURUSD", "EURO FX", extreme_threshold=95), "Crowded LONG")


def test_markers_do_not_appear_during_warmup():
    df = _merged(95, 60)
    early = df.copy()
    early.loc[:ZONE_WARMUP_WEEKS, ["52-Week Percentile"]] = 100.0
    early.loc[:ZONE_WARMUP_WEEKS, ["Net_Pct_of_OI"]] = 60.0
    fig = build_comparison_chart(early.iloc[:ZONE_WARMUP_WEEKS - 1].reset_index(drop=True),
                                 "EURUSD", "EURO FX")
    assert not _markers(fig, "Crowded")


def _line(fig, name, row_y):
    return [t for t in fig.data if t.name == name and t.yaxis == row_y]


def test_zone_lines_evolve_and_skip_warmup():
    df = _merged(50, 0.0)
    fig = build_comparison_chart(df, "EURUSD", "EURO FX")
    (hi,) = _line(fig, "Historical P90", "y2")
    y = np.asarray(hi.y, dtype=float)
    assert np.isnan(y[: ZONE_WARMUP_WEEKS - 1]).all()
    assert len(np.unique(y[~np.isnan(y)])) > 1


def test_inverted_dxy_panel_upper_line_is_negated_historical_p10():
    df = _merged(50, 0.0)
    fig = build_comparison_chart(df, "EURUSD", "EURO FX", invert_dxy=True)
    (upper,) = _line(fig, "Historical P90", "y3")
    np.testing.assert_allclose(np.asarray(upper.y, dtype=float), -df["OI Zone Lo_dxy"].to_numpy(),
                               equal_nan=True)


def test_zone_lines_hidden_when_toggle_is_off():
    fig = build_comparison_chart(_merged(50, 0.0), "EURUSD", "EURO FX", show_extreme_zones=False)
    assert not [t for t in fig.data if t.name and t.name.startswith("Historical")]


def test_stacked_chart_has_no_crosshair_by_default():
    fig = build_stacked_chart(_merged(50, 0.0), "EURUSD", "EURO FX")
    assert fig.layout.hoversubplots is None


def test_apply_shared_crosshair_enables_it():
    fig = apply_shared_crosshair(build_stacked_chart(_merged(50, 0.0), "EURUSD", "EURO FX"))
    assert fig.layout.hoversubplots == "axis"
