"""Seeded synthetic OHLCV generation and strict input validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
import math
import random
from typing import Callable, Sequence

from .models import Bar

CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class SyntheticConfig:
    symbols: tuple[str, ...] = ("SYNTH_A",)
    periods: int = 252
    seed: int = 7
    initial_price: Decimal = Decimal("100")
    drift: float = 0.0002
    volatility: float = 0.01
    correlation: float = 0.25
    interval: timedelta = timedelta(days=1)


def _validate_config(config: SyntheticConfig, start: datetime) -> None:
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("start must be timezone-aware")
    if not config.symbols or len(set(config.symbols)) != len(config.symbols):
        raise ValueError("symbols must be non-empty and unique")
    if config.periods < 1 or config.initial_price <= 0 or config.interval <= timedelta(0):
        raise ValueError("periods, initial_price, and interval must be positive")
    if config.volatility < 0 or not (-1 / max(1, len(config.symbols) - 1) < config.correlation < 1):
        raise ValueError("volatility/correlation is unsupported")


def generate_bars(
    config: SyntheticConfig,
    *,
    start: datetime,
    clock: Callable[[], datetime] | None = None,
) -> list[Bar]:
    """Generate reproducible correlated bars; ``clock`` enables an injected start."""
    if clock is not None:
        start = clock()
    _validate_config(config, start)
    rng = random.Random(config.seed)
    prices = [float(config.initial_price)] * len(config.symbols)
    result: list[Bar] = []
    common_weight = math.sqrt(max(0.0, config.correlation))
    independent_weight = math.sqrt(1.0 - max(0.0, config.correlation))
    # Negative equicorrelation is deliberately rejected above for this simple factor model.
    if config.correlation < 0:
        raise ValueError("negative correlation is not implemented")
    for index in range(config.periods):
        timestamp = start + index * config.interval
        common = rng.gauss(0, 1)
        for asset, symbol in enumerate(config.symbols):
            opening = prices[asset]
            shock = common_weight * common + independent_weight * rng.gauss(0, 1)
            closing = opening * math.exp(config.drift - config.volatility**2 / 2 + config.volatility * shock)
            span = abs(rng.gauss(0, config.volatility / 2))
            high = max(opening, closing) * (1 + span)
            low = min(opening, closing) * max(0.01, 1 - span)
            volume = max(1, int(rng.lognormvariate(11, 0.35)))
            q = lambda value: Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_EVEN)
            result.append(Bar(timestamp, symbol, q(opening), q(high), q(low), q(closing), volume))
            prices[asset] = closing
    validate_bars(result)
    return result


def validate_bars(bars: Sequence[Bar]) -> None:
    if not bars:
        raise ValueError("bars cannot be empty")
    seen: set[tuple[datetime, str]] = set()
    last_by_symbol: dict[str, datetime] = {}
    last_timestamp: datetime | None = None
    for bar in bars:
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            raise ValueError("all timestamps must be timezone-aware")
        key = (bar.timestamp, bar.symbol)
        if key in seen:
            raise ValueError(f"duplicate bar: {key}")
        seen.add(key)
        if last_timestamp is not None and bar.timestamp < last_timestamp:
            raise ValueError("bars must be globally chronological")
        last_timestamp = bar.timestamp
        if bar.timestamp <= last_by_symbol.get(bar.symbol, datetime.min.replace(tzinfo=bar.timestamp.tzinfo)):
            raise ValueError(f"bars are not chronological for {bar.symbol}")
        last_by_symbol[bar.symbol] = bar.timestamp
        if not bar.symbol or bar.volume < 0 or min(bar.open, bar.high, bar.low, bar.close) <= 0:
            raise ValueError("symbol, prices, and volume must be valid")
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close) or bar.low > bar.high:
            raise ValueError("invalid OHLC relationship")
