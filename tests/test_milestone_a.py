from datetime import datetime, timezone
from decimal import Decimal
import pytest
from quant_research.data import Bar, synthetic_bars, validate_bars
from quant_research.engine import BuyAndHold, Momentum, run_backtest


def test_generator_is_deterministic_and_correlated_multi_asset():
    a = synthetic_bars(symbols=("A", "B"), periods=20, seed=11)
    assert a == synthetic_bars(symbols=("A", "B"), periods=20, seed=11)
    assert a != synthetic_bars(symbols=("A", "B"), periods=20, seed=12)
    assert all(x.timestamp.tzinfo is not None for x in a)


def test_validation_rejects_duplicate_and_bad_ohlc():
    row = Bar(datetime(2024, 1, 1, tzinfo=timezone.utc), "A", 10, 11, 9, 10, 1)
    with pytest.raises(ValueError, match="duplicate"):
        validate_bars([row, row])
    with pytest.raises(ValueError, match="OHLC"):
        validate_bars([Bar(row.timestamp, "A", 10, 9, 8, 10, 1)])


def test_next_bar_execution_is_causal_under_adversarial_close():
    t = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars = synthetic_bars(periods=8, start=t, seed=3)
    altered = list(bars)
    b = altered[-1]
    altered[-1] = Bar(b.timestamp, b.symbol, b.open, 100000, b.low, 100000, b.volume)
    first = run_backtest(bars, Momentum(lookback=1))
    second = run_backtest(altered, Momentum(lookback=1))
    assert first.fills == second.fills  # final close can only affect an order beyond dataset


def test_accounting_conserves_equity_and_fees():
    bars = synthetic_bars(periods=4, volatility=0, drift=0)
    result = run_backtest(bars, BuyAndHold(2), initial_cash=Decimal("1000"), fee_rate=Decimal("0.01"))
    assert len(result.fills) == 1
    assert result.portfolio.cash == Decimal("798.00")
    assert result.portfolio.positions["SYN"] == 2
    assert result.equity[-1][1] == Decimal("998.00")
    assert result.portfolio.fees == Decimal("2.00")


def test_insufficient_cash_never_goes_negative():
    result = run_backtest(synthetic_bars(periods=3), BuyAndHold(100), initial_cash=Decimal("10"))
    assert result.fills == ()
    assert result.portfolio.cash == Decimal("10.00")
