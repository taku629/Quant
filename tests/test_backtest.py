from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_research.backtest import BacktestConfig, SimulationError, run_backtest
from quant_research.data import DataValidationError
from quant_research.models import Bar
from quant_research.strategy import BuyAndHold, Momentum


START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def bars(prices: list[tuple[str, str]]) -> list[Bar]:
    return [Bar(START + timedelta(days=i), "A", Decimal(op), max(Decimal(op), Decimal(cl)),
                min(Decimal(op), Decimal(cl)), Decimal(cl), 100) for i, (op, cl) in enumerate(prices)]


def test_signal_fills_only_at_next_open_not_known_close() -> None:
    # The first close is 1, but the next executable price gaps to 100.
    result = run_backtest(bars([("1", "1"), ("100", "100")]), BuyAndHold(),
                          BacktestConfig(Decimal("200"), 1, Decimal("0")))
    assert result.fills[0].signal_at == START
    assert result.fills[0].filled_at == START + timedelta(days=1)
    assert result.fills[0].price == Decimal("100")
    assert result.final_cash == Decimal("100.00")


def test_fee_and_equity_conservation() -> None:
    result = run_backtest(bars([("10", "10"), ("10", "11"), ("11", "9"), ("9", "9")]),
                          Momentum(1), BacktestConfig(Decimal("100"), 2, Decimal("100")))
    assert [(f.side.value, f.price, f.fee) for f in result.fills] == [
        ("buy", Decimal("11"), Decimal("0.22")), ("sell", Decimal("9"), Decimal("0.18"))]
    assert result.positions["A"] == 0
    assert result.realized_pnl == Decimal("-4.40")
    assert result.final_equity == Decimal("95.60")
    assert all(point.equity == point.cash + point.holdings for point in result.equity_curve)


def test_insufficient_cash_fails_loudly() -> None:
    with pytest.raises(SimulationError, match="insufficient cash"):
        run_backtest(bars([("10", "10"), ("11", "11")]), BuyAndHold(),
                     BacktestConfig(Decimal("5"), 1, Decimal("0")))


def test_global_out_of_order_input_is_rejected() -> None:
    ordered = bars([("10", "10"), ("11", "11")])
    with pytest.raises(DataValidationError, match="not chronological"):
        run_backtest(list(reversed(ordered)), BuyAndHold())
