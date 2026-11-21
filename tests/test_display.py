import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import data_processor
from charts import build_comparison_chart, build_heatmap_chart, build_overlay_chart, build_stacked_chart
from cftc_api import expanding_zone

N = 220


def _merged(base):
    df = pd.DataFrame({
        "Date": pd.date_range("2018-01-02", periods=N, freq="7D"),
        "close": np.linspace(base, base * 1.1, N),
        "Net_Pct_of_OI": np.sin(np.linspace(0, 30, N)) * 10,
        "Net_Pct_of_OI_dxy": np.cos(np.linspace(0, 30, N)) * 15,
        "52-Week Percentile": np.full(N, 50.0),
    })
    df["OI Zone Lo"], df["OI Zone Hi"] = expanding_zone(df["Net_Pct_of_OI"])
    df["OI Zone Lo_dxy"], df["OI Zone Hi_dxy"] = expanding_zone(df["Net_Pct_of_OI_dxy"])
    return df


def _price_templates(fig):
    return [t.hovertemplate for t in fig.data if t.hovertemplate and "Price" in t.hovertemplate]


@pytest.mark.parametrize("pair, cot, base, decimals", [
    ("XAUUSD", "GOLD", 2000.0, 2),
    ("USDJPY", "JAPANESE YEN", 150.0, 3),
    ("EURUSD", "EURO FX", 1.1, 5),
])
@pytest.mark.parametrize("builder", [build_comparison_chart, build_stacked_chart, build_overlay_chart])
def test_chart_hover_uses_instrument_precision(builder, pair, cot, base, decimals):
    templates = _price_templates(builder(_merged(base), pair, cot))
    assert templates
    assert all(f":.{decimals}f}}" in t for t in templates)


def test_heatmap_price_text_uses_instrument_precision():
    fig = build_heatmap_chart(_merged(2000.0), "XAUUSD", "GOLD")
    price_heatmap = fig.data[2]
    assert ":.2f}" in price_heatmap.hovertemplate
    assert all(len(v.split(".")[-1]) <= 2 for v in price_heatmap.text.ravel() if v)


def _tile_value(pair, close, prev):
    def app():
        import pandas as pd
        from ui_components import render_momentum_metrics
        df = pd.DataFrame({"close": [PREV, CLOSE]})
        render_momentum_metrics(df, pd.DataFrame(), pd.DataFrame(), PAIR, "X")
    script = f"PREV, CLOSE, PAIR = {prev!r}, {close!r}, {pair!r}\n" + _fn_source(app)
    at = AppTest.from_string(script).run()
    assert not at.exception
    return at.metric[0].value


def _fn_source(fn):
    import inspect, textwrap
    body = textwrap.dedent(inspect.getsource(fn)).split("\n", 1)[1]
    return textwrap.dedent(body)


def test_tile_gold_two_decimals():
    assert _tile_value("XAUUSD", 4012.3456, 4000.0) == "4012.35"


def test_tile_jpy_three_decimals():
    assert _tile_value("USDJPY", 150.1234, 150.0) == "150.123"


@pytest.fixture
def no_data(monkeypatch):
    monkeypatch.setattr(data_processor, "get_cot_data", lambda _n: pd.DataFrame())
    monkeypatch.setattr(data_processor, "get_forex_data", lambda *a, **k: pd.DataFrame())


def _sidebar_captions(pair):
    at = AppTest.from_file("app.py", default_timeout=60).run()
    at.sidebar.selectbox(key="main_pair").set_value(pair).run()
    return [c.value for c in at.sidebar.caption]


def test_gold_selected_shows_managed_money_notice(no_data):
    assert any("Managed Money" in c for c in _sidebar_captions("XAUUSD"))


def test_currency_selected_shows_no_notice(no_data):
    assert not any("Managed Money" in c for c in _sidebar_captions("EURUSD"))
