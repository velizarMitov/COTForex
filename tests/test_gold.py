import io
import json
from urllib.parse import parse_qs, urlparse

import pytest

import cftc_api
from cftc_api import _normalize_currency_name, get_cot_data
from symbols import COT_TO_MT5, MT5_TO_COT, price_decimals


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _gold_rows():
    return [
        {"report_date_as_yyyy_mm_dd": "2024-01-09T00:00:00.000",
         "m_money_positions_long_all": "120", "m_money_positions_short_all": "20",
         "pct_of_oi_m_money_long_all": "30.0", "pct_of_oi_m_money_short_all": "5.0"},
        {"report_date_as_yyyy_mm_dd": "2024-01-02T00:00:00.000",
         "m_money_positions_long_all": "100", "m_money_positions_short_all": "40",
         "pct_of_oi_m_money_long_all": "25.0", "pct_of_oi_m_money_short_all": "10.0"},
    ]


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake_urlopen(url, timeout=None):
        seen["url"] = url
        return _FakeResponse(json.dumps(seen.get("rows", [])).encode())

    monkeypatch.setattr(cftc_api, "urlopen", fake_urlopen)
    return seen


def test_gold_request_targets_disaggregated_managed_money(captured):
    captured["rows"] = _gold_rows()
    get_cot_data("GOLD")

    url = urlparse(captured["url"])
    query = parse_qs(url.query)
    assert url.path.endswith("/72hh-3qpy.json")
    assert query["$where"] == ["cftc_contract_market_code = '088691'"]
    for field in ("m_money_positions_long_all", "m_money_positions_short_all",
                  "pct_of_oi_m_money_long_all", "pct_of_oi_m_money_short_all"):
        assert field in query["$select"][0]


def test_gold_metrics_match_currency_shape(captured):
    captured["rows"] = _gold_rows()
    df = get_cot_data("GOLD")

    assert list(df["Net Position"]) == [60, 100]
    assert list(df["Net_Pct_of_OI"]) == [15.0, 25.0]
    for col in ("Net Position Change", "52-Week Percentile", "OI Zone Lo", "OI Zone Hi", "Crowded Signal"):
        assert col in df.columns


def test_currency_request_still_uses_tff(captured):
    captured["rows"] = []
    get_cot_data("EURO FX")
    url = urlparse(captured["url"])
    assert url.path.endswith("/gpe5-46if.json")
    assert parse_qs(url.query)["$where"] == ["contract_market_name = 'EURO FX'"]


@pytest.mark.parametrize("name", ["GOLD", "gold", "XAUUSD", "XAU/USD"])
def test_gold_is_an_accepted_market_name(name):
    assert _normalize_currency_name(name) == "GOLD"


def test_unsupported_market_lists_gold():
    with pytest.raises(ValueError, match="GOLD"):
        _normalize_currency_name("BITCOIN")


def test_symbol_mapping_includes_gold():
    assert COT_TO_MT5["GOLD"] == "XAUUSD"
    assert MT5_TO_COT["XAUUSD"] == "GOLD"


@pytest.mark.parametrize("symbol, decimals", [
    ("XAUUSD", 2), ("USDJPY", 3), ("EURUSD", 5), ("AUDUSD", 5),
])
def test_price_decimals(symbol, decimals):
    assert price_decimals(symbol) == decimals
