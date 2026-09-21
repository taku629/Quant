from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_research.backtest import ExecutionConfig, run_backtest
from quant_research.models import Bar
from quant_research.strategy import BuyAndHold, MovingAverageCross


def bars(prices: list[tuple[str, str]]) -> list[Bar]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Bar(start + timedelta(days=i), "A", Decimal(open_), max(Decimal(open_), Decimal(close)),
            min(Decimal(open_), Decimal(close)), Decimal(close), 1000)
        for i, (open_, close) in enumerate(prices)
    ]


def test_close_signal_fills_at_next_open_not_same_close() -> None:
    data = bars([("10", "1000"), ("20", "20"), ("30", "30")])
    result = run_backtest(data, BuyAndHold(2), initial_cash=Decimal("100"),
                          execution=ExecutionConfig(Decimal("0"), Decimal("0")))
    assert len(result.fills) == 1
    assert result.fills[0].price == Decimal("20")
    assert result.fills[0].filled_at > result.fills[0].signal_at
    assert result.final_cash == Decimal("60.00")
    assert result.final_equity == Decimal("120.00")


def test_future_close_cannot_change_prior_fill() -> None:
    base = bars([("10", "10"), ("11", "11"), ("12", "12")])
    adversarial = bars([("10", "10"), ("11", "999999"), ("12", "12")])
    config = ExecutionConfig(Decimal("0"), Decimal("0"))
    assert run_backtest(base, BuyAndHold(1), execution=config).fills[0] == \
        run_backtest(adversarial, BuyAndHold(1), execution=config).fills[0]


def test_fees_cash_and_pnl_are_conserved() -> None:
    class RoundTrip:
        def target(self, bar: Bar, current_quantity: int) -> int:
            return 2 if bar.timestamp.day == 1 else 0

    result = run_backtest(bars([("10", "10"), ("10", "10"), ("12", "12")]), RoundTrip(),
                          initial_cash=Decimal("100"),
                          execution=ExecutionConfig(Decimal("1"), Decimal("0")))
    assert [fill.price for fill in result.fills] == [Decimal("10"), Decimal("12")]
    assert result.positions["A"] == 0
    assert result.total_fees == Decimal("2.00")
    assert result.final_cash == Decimal("102.00")
    assert result.realized_pnl == Decimal("2.00")
    assert result.final_equity - result.initial_cash == result.realized_pnl


def test_open_position_pnl_reconciles_to_equity() -> None:
    result = run_backtest(bars([("10", "10"), ("10", "10"), ("12", "12")]), BuyAndHold(3),
                          initial_cash=Decimal("100"),
                          execution=ExecutionConfig(Decimal("0.25"), Decimal("1")))
    assert result.realized_pnl + result.unrealized_pnl == result.final_equity - result.initial_cash


def test_insufficient_cash_is_rejected_without_negative_balance() -> None:
    result = run_backtest(bars([("10", "10"), ("10", "10")]), BuyAndHold(100), initial_cash=Decimal("20"))
    assert result.fills == ()
    assert result.final_cash == Decimal("20.00")
    assert result.positions == {}


def test_last_bar_signal_is_reported_unfilled() -> None:
    result = run_backtest(bars([("10", "10")]), BuyAndHold(1))
    assert len(result.unfilled_orders) == 1
    assert result.fills == ()


def test_ma_configuration_and_target_validation() -> None:
    with pytest.raises(ValueError):
        MovingAverageCross(2, 2)

    class Invalid:
        def target(self, bar: Bar, current_quantity: int) -> int:
            return -1

    with pytest.raises(ValueError, match="non-negative"):
        run_backtest(bars([("10", "10")]), Invalid())
