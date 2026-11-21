from types import SimpleNamespace

import pytest

import mt5_api


@pytest.fixture
def terminal(monkeypatch):
    """Fake terminal exposing the given symbol names."""
    def install(names):
        known = {n.upper(): SimpleNamespace(name=n) for n in names}
        monkeypatch.setattr(mt5_api.mt5, "symbol_info", lambda n: known.get(n.upper()))
        monkeypatch.setattr(
            mt5_api.mt5, "symbols_get",
            lambda pattern: [v for v in known.values() if pattern.strip("*").upper() in v.name.upper()],
        )
    return install


def test_exact_name_wins(terminal):
    terminal(["XAUUSD", "GOLD"])
    assert mt5_api.resolve_symbol("XAUUSD") == "XAUUSD"


def test_broker_that_calls_gold_gold(terminal):
    terminal(["EURUSD", "GOLD"])
    assert mt5_api.resolve_symbol("XAUUSD") == "GOLD"


def test_suffixed_name_found_by_search(terminal):
    terminal(["XAUUSD_i", "XAUEUR"])
    assert mt5_api.resolve_symbol("XAUUSD") == "XAUUSD_i"


def test_no_match_returns_none(terminal):
    terminal(["EURUSD", "XAUEUR"])
    assert mt5_api.resolve_symbol("XAUUSD") is None


def test_plain_pairs_are_not_aliased(terminal):
    terminal(["EURUSD"])
    assert mt5_api.resolve_symbol("EURUSD") == "EURUSD"
    assert mt5_api.resolve_symbol("GBPUSD") is None


def test_fetch_returns_empty_when_symbol_missing(terminal, monkeypatch):
    terminal(["EURUSD"])
    monkeypatch.setattr(mt5_api, "init_mt5_connection", lambda: True)
    assert mt5_api.fetch_forex_data("XAUUSD").empty
