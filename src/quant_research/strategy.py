from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .models import Bar, Side


class Strategy(Protocol):
    def signal(self, history: Sequence[Bar], position: int) -> Side | None: ...


@dataclass(frozen=True, slots=True)
class BuyAndHold:
    """Buy once; the order is executed at the following bar's open."""
    def signal(self, history: Sequence[Bar], position: int) -> Side | None:
        return Side.BUY if len(history) == 1 and position == 0 else None


@dataclass(frozen=True, slots=True)
class Momentum:
    lookback: int = 5

    def __post_init__(self) -> None:
        if self.lookback < 1:
            raise ValueError("lookback must be positive")

    def signal(self, history: Sequence[Bar], position: int) -> Side | None:
        if len(history) <= self.lookback:
            return None
        rising = history[-1].close > history[-1 - self.lookback].close
        if rising and position == 0:
            return Side.BUY
        if not rising and position > 0:
            return Side.SELL
        return None
