from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant_research.data import SyntheticConfig, generate_bars, validate_bars


START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_generation_is_seeded_multi_asset_and_valid() -> None:
    config = SyntheticConfig(symbols=("A", "B"), periods=12, seed=123, correlation=0.5)
    first = generate_bars(config, start=START)
    second = generate_bars(config, start=START)
    assert first == second
    assert len(first) == 24
    assert {bar.symbol for bar in first} == {"A", "B"}


def test_clock_is_injected_and_timezone_required() -> None:
    config = SyntheticConfig(periods=2)
    assert generate_bars(config, start=START, clock=lambda: START)[0].timestamp == START
    with pytest.raises(ValueError, match="timezone-aware"):
        generate_bars(config, start=datetime(2024, 1, 1))


def test_validation_rejects_duplicate_bad_ohlc_and_out_of_order() -> None:
    bars = generate_bars(SyntheticConfig(periods=2), start=START)
    with pytest.raises(ValueError, match="duplicate"):
        validate_bars([bars[0], bars[0]])
    with pytest.raises(ValueError, match="OHLC"):
        validate_bars([replace(bars[0], high=Decimal("1"))])
    with pytest.raises(ValueError, match="globally chronological"):
        validate_bars(list(reversed(bars)))


@pytest.mark.parametrize("correlation", [-0.1, 1.0])
def test_unsupported_correlation_fails(correlation: float) -> None:
    with pytest.raises(ValueError, match="correlation"):
        generate_bars(SyntheticConfig(periods=2, correlation=correlation), start=START)
