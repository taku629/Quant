from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Mapping, Sequence

from .data import validate_bars
from .models import Bar, EquityPoint, Fill, Order, Side
from .strategy import Strategy

CENT = Decimal("0.01")


class SimulationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: Decimal = Decimal("10000.00")
    order_quantity: int = 1
    fee_bps: Decimal = Decimal("5")

    def __post_init__(self) -> None:
        if self.initial_cash < 0 or self.order_quantity <= 0 or self.fee_bps < 0:
            raise ValueError("cash/fees must be non-negative and quantity positive")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    initial_cash: Decimal
    final_cash: Decimal
    positions: Mapping[str, int]
    fills: tuple[Fill, ...]
    equity_curve: tuple[EquityPoint, ...]
    realized_pnl: Decimal
    fees: Decimal

    @property
    def final_equity(self) -> Decimal:
        return self.equity_curve[-1].equity

    @property
    def total_return(self) -> Decimal:
        if not self.initial_cash:
            return Decimal(0)
        return (self.final_equity / self.initial_cash) - Decimal(1)


def _cent(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


def run_backtest(bars: Sequence[Bar], strategy: Strategy,
                 config: BacktestConfig = BacktestConfig()) -> BacktestResult:
    """Run causal close-signal/next-open execution with long-only cash accounting.

    Bars at a timestamp are first used to execute orders submitted on an earlier
    timestamp. Their closes are then revealed to the strategy. This prevents a
    signal from filling on the close that created it.
    """
    validate_bars(bars)
    ordered = sorted(bars, key=lambda b: (b.timestamp, b.symbol))
    if list(bars) != ordered:
        raise SimulationError("input must be globally sorted by timestamp and symbol")
    cash = _cent(config.initial_cash)
    positions: dict[str, int] = defaultdict(int)
    average_cost: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    histories: dict[str, list[Bar]] = defaultdict(list)
    pending: dict[str, Order] = {}
    fills: list[Fill] = []
    curve: list[EquityPoint] = []
    latest: dict[str, Decimal] = {}
    realized = Decimal(0)
    fees_total = Decimal(0)
    order_id = 0

    timestamps = sorted({bar.timestamp for bar in ordered})
    by_time = {ts: [bar for bar in ordered if bar.timestamp == ts] for ts in timestamps}
    for timestamp in timestamps:
        current = by_time[timestamp]
        for bar in current:
            order = pending.pop(bar.symbol, None)
            if order is not None:
                if order.submitted_at >= timestamp:
                    raise SimulationError("order cannot fill at or before its signal")
                gross = _cent(bar.open * order.quantity)
                fee = _cent(gross * config.fee_bps / Decimal(10_000))
                if order.side is Side.BUY:
                    if gross + fee > cash:
                        raise SimulationError(f"insufficient cash for order {order.order_id}")
                    old_qty = positions[bar.symbol]
                    average_cost[bar.symbol] = ((average_cost[bar.symbol] * old_qty + gross + fee)
                                                / (old_qty + order.quantity))
                    cash -= gross + fee
                    positions[bar.symbol] += order.quantity
                else:
                    if order.quantity > positions[bar.symbol]:
                        raise SimulationError(f"insufficient position for order {order.order_id}")
                    cash += gross - fee
                    realized += gross - fee - average_cost[bar.symbol] * order.quantity
                    positions[bar.symbol] -= order.quantity
                    if positions[bar.symbol] == 0:
                        average_cost[bar.symbol] = Decimal(0)
                cash = _cent(cash)
                fees_total += fee
                fills.append(Fill(order.order_id, bar.symbol, order.side, order.quantity,
                                  order.submitted_at, timestamp, bar.open, fee))

        for bar in current:
            latest[bar.symbol] = bar.close
            histories[bar.symbol].append(bar)
            side = strategy.signal(tuple(histories[bar.symbol]), positions[bar.symbol])
            if side is not None and bar.symbol not in pending:
                order_id += 1
                qty = config.order_quantity if side is Side.BUY else positions[bar.symbol]
                if qty > 0:
                    pending[bar.symbol] = Order(order_id, bar.symbol, side, qty, timestamp)

        holdings = _cent(sum((latest[s] * q for s, q in positions.items()), Decimal(0)))
        equity = _cent(cash + holdings)
        if equity != _cent(cash + sum((latest[s] * q for s, q in positions.items()), Decimal(0))):
            raise AssertionError("portfolio conservation violated")
        curve.append(EquityPoint(timestamp, cash, holdings, equity))

    return BacktestResult(_cent(config.initial_cash), cash, dict(positions), tuple(fills),
                          tuple(curve), _cent(realized), _cent(fees_total))
