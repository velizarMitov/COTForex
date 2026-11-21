import numpy as np
import pandas as pd
import pytest

from charts import NEG, POS, _rgba, apply_shared_crosshair, build_comparison_chart, build_stacked_chart

N = 80
CROWDED_WEEK = 40


def _merged(pct_at_extreme):
    pct = np.full(N, 50.0)
    pct[CROWDED_WEEK:CROWDED_WEEK + 4] = pct_at_extreme
    return pd.DataFrame({
        "Date": pd.date_range("2022-01-04", periods=N, freq="7D"),
        "close": np.linspace(1.0, 1.2, N),
        "Net_Pct_of_OI": np.sin(np.linspace(0, 6, N)) * 20,
        "Net_Pct_of_OI_dxy": np.cos(np.linspace(0, 6, N)) * 15,
        "52-Week Percentile": pct,
    })


def _marker(fig, prefix):
    traces = [t for t in fig.data if t.name and t.name.startswith(prefix)]
    assert len(traces) == 1, f"expected one '{prefix}' trace"
    return traces[0]


def _assert_marker(fig, df, prefix, symbol, color, above):
    trace = _marker(fig, prefix)
    assert trace.marker.symbol == symbol
    assert trace.marker.color == _rgba(color, 0.95)
    price = df["close"].iloc[CROWDED_WEEK]
    assert (trace.y[0] > price) if above else (trace.y[0] < price)


@pytest.mark.parametrize("pair, cot, pct, prefix, symbol, color, above", [
    ("EURUSD", "EURO FX", 95, "Crowded LONG", "triangle-down", NEG, True),
    ("EURUSD", "EURO FX", 5, "Crowded SHORT", "triangle-up", POS, False),
    ("USDJPY", "JAPANESE YEN", 95, "Crowded LONG", "triangle-up", POS, False),
    ("USDCHF", "SWISS FRANC", 5, "Crowded SHORT", "triangle-down", NEG, True),
])
def test_marker_points_to_pair_unwind_direction(pair, cot, pct, prefix, symbol, color, above):
    df = _merged(pct)
    fig = build_comparison_chart(df, pair, cot)
    _assert_marker(fig, df, prefix, symbol, color, above)


def test_marker_label_names_futures_side():
    fig = build_comparison_chart(_merged(95), "USDJPY", "JAPANESE YEN")
    assert _marker(fig, "Crowded LONG").name.startswith("Crowded LONG Japanese Yen futures")


def test_stacked_chart_has_no_crosshair_by_default():
    fig = build_stacked_chart(_merged(50), "EURUSD", "EURO FX")
    assert fig.layout.hoversubplots is None


def test_apply_shared_crosshair_enables_it():
    fig = apply_shared_crosshair(build_stacked_chart(_merged(50), "EURUSD", "EURO FX"))
    assert fig.layout.hoversubplots == "axis"
