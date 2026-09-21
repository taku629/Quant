"""Causal strategies that see closes only through the current timestamp."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

from .models import Bar


class Strategy(Protocol):
    def target(self, bar: Bar, current_quantity: int) -> int: ...


@dataclass(slots=True)
class BuyAndHold:
    quantity: int = 10

    def target(self, bar: Bar, current_quantity: int) -> int:
        return self.quantity


@dataclass(slots=True)
class MovingAverageCross:
    short_window: int = 5
    long_window: int = 20
    quantity: int = 10
    _history: dict[str, deque[Decimal]] = field(default_factory=lambda: defaultdict(deque), init=False)

    def __post_init__(self) -> None:
        if not (0 < self.short_window < self.long_window) or self.quantity < 1:
            raise ValueError("require 0 < short_window < long_window and positive quantity")

    def target(self, bar: Bar, current_quantity: int) -> int:
        history = self._history[bar.symbol]
        history.append(bar.close)
        while len(history) > self.long_window:
            history.popleft()
        if len(history) < self.long_window:
            return 0
        values = list(history)
        short = sum(values[-self.short_window :]) / self.short_window
        long = sum(values) / self.long_window
        return self.quantity if short > long else 0
