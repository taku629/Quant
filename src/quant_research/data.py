"""Deterministic synthetic market data and strict validation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import random


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def validate_bars(bars: list[Bar]) -> None:
    """Reject malformed, duplicate, or non-chronological symbol/timestamp rows."""
    seen: set[tuple[str, datetime]] = set()
    last: dict[str, datetime] = {}
    for bar in bars:
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        key = (bar.symbol, bar.timestamp)
        if key in seen:
            raise ValueError(f"duplicate bar: {key}")
        if bar.symbol in last and bar.timestamp <= last[bar.symbol]:
            raise ValueError(f"bars are not chronological for {bar.symbol}")
        if not bar.symbol or not all(math.isfinite(x) and x > 0 for x in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError("symbol and prices must be finite and positive")
        if bar.volume < 0 or not math.isfinite(bar.volume):
            raise ValueError("volume must be finite and non-negative")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close) or bar.low > bar.high:
            raise ValueError("invalid OHLC relationship")
        seen.add(key)
        last[bar.symbol] = bar.timestamp


def synthetic_bars(*, symbols: tuple[str, ...] = ("SYN",), periods: int = 252,
                   start: datetime | None = None, seed: int = 7, volatility: float = 0.01,
                   drift: float = 0.0002, correlation: float = 0.35,
                   regime_at: int | None = None, regime_drift: float = -0.0002) -> list[Bar]:
    """Generate correlated daily geometric paths from an injected UTC clock.

    Prices are rounded to six decimals. ``correlation`` is a one-factor loading,
    rather than a promise of exact finite-sample correlation.
    """
    if periods < 1 or not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("periods and unique symbols are required")
    if volatility < 0 or not 0 <= correlation <= 1:
        raise ValueError("invalid volatility or correlation")
    start = start or datetime(2020, 1, 1, tzinfo=timezone.utc)
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("start must be timezone-aware")
    rng = random.Random(seed)
    prices = {s: 100.0 for s in symbols}
    rows: list[Bar] = []
    for i in range(periods):
        common = rng.gauss(0, 1)
        for symbol in symbols:
            previous = prices[symbol]
            shock = correlation * common + math.sqrt(1 - correlation**2) * rng.gauss(0, 1)
            active_drift = regime_drift if regime_at is not None and i >= regime_at else drift
            close = previous * math.exp(active_drift - volatility**2 / 2 + volatility * shock)
            intraday = abs(rng.gauss(0, volatility / 2))
            high = max(previous, close) * (1 + intraday)
            low = min(previous, close) / (1 + intraday)
            rows.append(Bar(start + timedelta(days=i), symbol, round(previous, 6), round(high, 6),
                            round(low, 6), round(close, 6), round(rng.uniform(1000, 10000), 3)))
            prices[symbol] = close
    rows.sort(key=lambda b: (b.timestamp, b.symbol))
    validate_bars_by_symbol(rows)
    return rows


def validate_bars_by_symbol(bars: list[Bar]) -> None:
    grouped: dict[str, list[Bar]] = {}
    for bar in bars:
        grouped.setdefault(bar.symbol, []).append(bar)
    for values in grouped.values():
        validate_bars(values)
