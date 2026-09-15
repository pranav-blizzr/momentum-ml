# src/momentum_ml/contracts.py
"""The only types that cross the boundary between momentum_ml and tradingbot.
Change these deliberately: bump CONTRACT_VERSION and update the bot's adapter in the same release."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class Trade:
    symbol: str
    ts_ns: int  # exchange timestamp, UTC nanoseconds
    price: float
    size: int
    conditions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    ts_ns: int
    bid: float
    ask: float
    bid_size: int
    ask_size: int


@dataclass(frozen=True, slots=True)
class DayContext:  # set once per symbol per session, updated by the bot
    symbol: str
    session_date: str  # "YYYY-MM-DD", US/Eastern trading date
    prev_close: float
    float_shares: int | None
    avg_volume_by_minute: tuple[float, ...]  # for time-of-day RVOL


@dataclass(frozen=True, slots=True)
class SetupEvent:
    strategy: str  # "mpb" | "hod" | "vwap_brp"
    symbol: str
    ts_ns: int
    trigger_px: float
    stop_px: float
    features: dict = field(default_factory=dict)


class Action(StrEnum):
    TAKE = "take"
    SKIP = "skip"
    SHADOW = "shadow"  # scored and logged, never traded


@dataclass(frozen=True, slots=True)
class Decision:
    setup: SetupEvent
    action: Action
    p: float | None  # calibrated probability, None if no model loaded
    ev_r: float | None
    model_id: str | None  # e.g. "mpb_v3@sha256:ab12…"
    library_version: str
    reasons: tuple[tuple[str, float], ...] = ()  # top SHAP contributions


class Engine(Protocol):
    """One instance per symbol. Pure: no sockets, files, clocks or threads.
    Same input stream in → same decisions out, live or replay."""

    def set_context(self, ctx: DayContext) -> None: ...
    def on_trade(self, trade: Trade) -> list[Decision]: ...
    def on_quote(self, quote: Quote) -> None: ...