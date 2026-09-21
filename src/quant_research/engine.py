"""Causal next-open bar simulator with long-only cash accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Protocol

from .data import Bar, validate_bars_by_symbol

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


class Strategy(Protocol):
    def target(self, history: tuple[Bar, ...]) -> int: ...


@dataclass(frozen=True)
class BuyAndHold:
    quantity: int = 1
    def target(self, history: tuple[Bar, ...]) -> int:
        return self.quantity


@dataclass(frozen=True)
class Momentum:
    lookback: int = 5
    quantity: int = 1
    def target(self, history: tuple[Bar, ...]) -> int:
        if len(history) <= self.lookback:
            return 0
        return self.quantity if history[-1].close > history[-1 - self.lookback].close else 0


@dataclass(frozen=True)
class MeanReversion:
    lookback: int = 5
    quantity: int = 1
    threshold: float = 0.01
    def target(self, history: tuple[Bar, ...]) -> int:
        if len(history) <= self.lookback: return 0
        baseline = sum(x.close for x in history[-self.lookback-1:-1]) / self.lookback
        return self.quantity if history[-1].close < baseline * (1-self.threshold) else 0


@dataclass(frozen=True)
class Fill:
    timestamp: datetime
    symbol: str
    quantity: int
    price: Decimal
    fee: Decimal
    signal_timestamp: datetime


@dataclass
class Portfolio:
    initial_cash: Decimal
    cash: Decimal = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)
    average_cost: dict[str, Decimal] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        self.cash = money(self.initial_cash)
        if self.cash < 0:
            raise ValueError("cash cannot be negative")

    def apply(self, fill: Fill) -> None:
        old = self.positions.get(fill.symbol, 0)
        new = old + fill.quantity
        if new < 0:
            raise ValueError("shorting is unsupported")
        notional = money(fill.price * fill.quantity)
        new_cash = money(self.cash - notional - fill.fee)
        if new_cash < 0:
            raise ValueError("insufficient cash")
        if fill.quantity > 0:
            total_cost = self.average_cost.get(fill.symbol, Decimal("0")) * old + fill.price * fill.quantity
            self.average_cost[fill.symbol] = total_cost / new
        elif fill.quantity < 0:
            self.realized_pnl = money(self.realized_pnl + (fill.price - self.average_cost[fill.symbol]) * (-fill.quantity) - fill.fee)
            if new == 0:
                self.average_cost.pop(fill.symbol, None)
        self.cash, self.positions[fill.symbol] = new_cash, new
        self.fees = money(self.fees + fill.fee)

    def equity(self, prices: dict[str, Decimal]) -> Decimal:
        return money(self.cash + sum(prices[s] * q for s, q in self.positions.items()))


@dataclass(frozen=True)
class Result:
    fills: tuple[Fill, ...]
    equity: tuple[tuple[datetime, Decimal], ...]
    portfolio: Portfolio


def run_backtest(bars: list[Bar], strategy: Strategy, *, initial_cash: Decimal = Decimal("10000"),
                 fee_rate: Decimal = Decimal("0.001")) -> Result:
    """Signal after close t, execute at open t+1; never use same-bar future fields."""
    validate_bars_by_symbol(bars)
    if fee_rate < 0:
        raise ValueError("fee_rate cannot be negative")
    portfolio, fills = Portfolio(initial_cash), []
    histories: dict[str, list[Bar]] = {}
    pending: dict[str, tuple[int, datetime]] = {}
    marks: dict[str, Decimal] = {}
    curve: list[tuple[datetime, Decimal]] = []
    for timestamp in sorted({b.timestamp for b in bars}):
        current = {b.symbol: b for b in bars if b.timestamp == timestamp}
        for symbol, bar in sorted(current.items()):
            if symbol in pending:
                target, signal_time = pending.pop(symbol)
                quantity = target - portfolio.positions.get(symbol, 0)
                price = Decimal(str(bar.open))
                fee = money(abs(price * quantity) * fee_rate)
                if quantity:
                    fill = Fill(timestamp, symbol, quantity, price, fee, signal_time)
                    try:
                        portfolio.apply(fill)
                    except ValueError as exc:
                        if str(exc) != "insufficient cash":
                            raise
                    else:
                        fills.append(fill)
            histories.setdefault(symbol, []).append(bar)
            target = strategy.target(tuple(histories[symbol]))
            if target < 0:
                raise ValueError("negative targets are unsupported")
            pending[symbol] = (target, timestamp)
            marks[symbol] = Decimal(str(bar.close))
        curve.append((timestamp, portfolio.equity(marks)))
    return Result(tuple(fills), tuple(curve), portfolio)
