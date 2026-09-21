"""Causal next-bar-open execution and authoritative long-only accounting."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from itertools import groupby
from typing import Iterable

from .data import validate_bars
from .models import Bar, Fill, Order, Side
from .strategy import Strategy

CENT = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    fee_fixed: Decimal = Decimal("0.25")
    fee_bps: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if self.fee_fixed < 0 or self.fee_bps < 0:
            raise ValueError("fees cannot be negative")


@dataclass(frozen=True, slots=True)
class EquityPoint:
    timestamp: datetime
    cash: Decimal
    holdings: Decimal
    equity: Decimal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    initial_cash: Decimal
    final_cash: Decimal
    positions: dict[str, int]
    average_costs: dict[str, Decimal]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_fees: Decimal
    fills: tuple[Fill, ...]
    equity_curve: tuple[EquityPoint, ...]
    unfilled_orders: tuple[Order, ...]

    @property
    def final_equity(self) -> Decimal:
        return self.equity_curve[-1].equity

    @property
    def total_return(self) -> Decimal:
        return self.final_equity / self.initial_cash - Decimal(1)


class _Ledger:
    def __init__(self, cash: Decimal) -> None:
        if cash <= 0:
            raise ValueError("initial cash must be positive")
        self.cash = _money(cash)
        self.positions: dict[str, int] = {}
        self.average_costs: dict[str, Decimal] = {}
        self.realized = Decimal(0)
        self.fees = Decimal(0)

    def execute(self, order: Order, bar: Bar, config: ExecutionConfig) -> Fill | None:
        notional = _money(bar.open * order.quantity)
        fee = _money(config.fee_fixed + notional * config.fee_bps / Decimal(10_000))
        held = self.positions.get(order.symbol, 0)
        if order.side is Side.BUY:
            if notional + fee > self.cash:  # Explicit rejection: never borrow cash.
                return None
            old_basis = self.average_costs.get(order.symbol, Decimal(0)) * held
            new_quantity = held + order.quantity
            self.cash = _money(self.cash - notional - fee)
            self.positions[order.symbol] = new_quantity
            # Buy fees are capitalized so realized + unrealized P&L includes every fee.
            # Keep per-unit cost unrounded: rounding it would lose part of a cent per
            # share and break the P&L/equity conservation identity.
            self.average_costs[order.symbol] = (old_basis + notional + fee) / new_quantity
        else:
            if order.quantity > held:  # Explicit rejection: never short.
                return None
            basis = self.average_costs[order.symbol]
            self.cash = _money(self.cash + notional - fee)
            self.realized = _money(self.realized + (bar.open - basis) * order.quantity - fee)
            remaining = held - order.quantity
            self.positions[order.symbol] = remaining
            if remaining == 0:
                self.average_costs.pop(order.symbol)
        self.fees = _money(self.fees + fee)
        return Fill(order.order_id, order.created_at, bar.timestamp, order.symbol, order.side, order.quantity, bar.open, fee)


def run_backtest(
    bars: Iterable[Bar],
    strategy: Strategy,
    *,
    initial_cash: Decimal = Decimal("10000"),
    execution: ExecutionConfig = ExecutionConfig(),
) -> BacktestResult:
    """Run a long-only simulation. A close-t signal fills only at the next bar's open."""
    materialized = list(bars)
    validate_bars(materialized)
    materialized.sort(key=lambda bar: (bar.timestamp, bar.symbol))
    ledger = _Ledger(initial_cash)
    pending: dict[str, Order] = {}
    fills: list[Fill] = []
    curve: list[EquityPoint] = []
    last_prices: dict[str, Decimal] = {}
    order_id = 0

    for timestamp, timestamp_bars in groupby(materialized, key=lambda bar: bar.timestamp):
        batch = list(timestamp_bars)
        # Phase 1: fill previously submitted orders. Current closes are not yet visible.
        for bar in batch:
            order = pending.pop(bar.symbol, None)
            if order is not None:
                fill = ledger.execute(order, bar, execution)
                if fill is not None:
                    fills.append(fill)
        # Phase 2: reveal closes and ask for targets, scheduling orders for a future bar.
        for bar in batch:
            last_prices[bar.symbol] = bar.close
            held = ledger.positions.get(bar.symbol, 0)
            target = strategy.target(bar, held)
            if not isinstance(target, int) or target < 0:
                raise ValueError("strategies must return a non-negative integer target")
            delta = target - held
            if delta:
                order_id += 1
                pending[bar.symbol] = Order(
                    order_id, bar.timestamp, bar.symbol, Side.BUY if delta > 0 else Side.SELL, abs(delta)
                )
        holdings = _money(sum((last_prices[s] * q for s, q in ledger.positions.items()), Decimal(0)))
        equity = _money(ledger.cash + holdings)
        if equity != _money(ledger.cash + holdings) or ledger.cash < 0 or any(q < 0 for q in ledger.positions.values()):
            raise AssertionError("portfolio accounting invariant violated")
        curve.append(EquityPoint(timestamp, ledger.cash, holdings, equity))

    unrealized = _money(sum((
        (last_prices[symbol] - ledger.average_costs[symbol]) * quantity
        for symbol, quantity in ledger.positions.items() if quantity
    ), Decimal(0)))
    return BacktestResult(
        _money(initial_cash), ledger.cash, dict(ledger.positions), dict(ledger.average_costs), ledger.realized,
        unrealized, ledger.fees, tuple(fills), tuple(curve), tuple(pending.values())
    )
