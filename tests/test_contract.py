"""Checks the boundary contract with tradingbot (porting plan §3)."""

import dataclasses

import pytest

import momentum_ml
from momentum_ml.contracts import CONTRACT_VERSION, Action, Decision, SetupEvent, Trade


def test_package_has_version():
    assert isinstance(momentum_ml.__version__, str) and momentum_ml.__version__


def test_contract_version_is_set():
    assert CONTRACT_VERSION == "1.0"


def test_contract_types_are_immutable():
    trade = Trade(symbol="TEST", ts_ns=1, price=10.0, size=100)
    with pytest.raises(dataclasses.FrozenInstanceError):
        trade.price = 11.0


def test_decision_round_trip():
    setup = SetupEvent(strategy="mpb", symbol="TEST", ts_ns=1, trigger_px=10.81, stop_px=10.64)
    d = Decision(
        setup=setup,
        action=Action.SHADOW,
        p=None,
        ev_r=None,
        model_id=None,
        library_version=momentum_ml.__version__,
    )
    assert d.action is Action.SHADOW and d.setup.stop_px < d.setup.trigger_px