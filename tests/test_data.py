from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant_research.data import DataValidationError, SyntheticConfig, generate_bars, validate_bars
from quant_research.models import Bar


NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_generation_is_seeded_timezone_aware_and_multi_asset() -> None:
    config = SyntheticConfig(("A", "B", "C"), periods=12, seed=42, correlation=0.4)
    first = generate_bars(config, lambda: NOW)
    second = generate_bars(config, lambda: NOW)
    assert first == second
    assert len(first) == 36
    assert {bar.symbol for bar in first} == {"A", "B", "C"}
    assert all(bar.timestamp.tzinfo is timezone.utc for bar in first)


def test_clock_is_injected_and_called_once() -> None:
    calls = 0
    def clock() -> datetime:
        nonlocal calls
        calls += 1
        return NOW
    generate_bars(SyntheticConfig(periods=2), clock)
    assert calls == 1


def test_validation_rejects_duplicates_and_bad_ohlc() -> None:
    bar = Bar(NOW, "A", Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), 1)
    with pytest.raises(DataValidationError, match="duplicate"):
        validate_bars([bar, bar])
    bad = Bar(NOW, "A", Decimal("10"), Decimal("9"), Decimal("8"), Decimal("10"), 1)
    with pytest.raises(DataValidationError, match="OHLC"):
        validate_bars([bad])


def test_invalid_correlation_and_naive_clock_fail() -> None:
    with pytest.raises(ValueError, match="correlation"):
        generate_bars(SyntheticConfig(("A", "B", "C"), periods=2, correlation=-0.9), lambda: NOW)
    with pytest.raises(ValueError, match="timezone"):
        generate_bars(SyntheticConfig(periods=2), lambda: datetime(2024, 1, 1))
