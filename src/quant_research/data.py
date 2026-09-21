from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Callable, Iterable

from .models import Bar

CENT = Decimal("0.01")


class DataValidationError(ValueError):
    """Raised when bars cannot be safely simulated."""


@dataclass(frozen=True, slots=True)
class SyntheticConfig:
    symbols: tuple[str, ...] = ("AAA",)
    periods: int = 100
    interval: timedelta = timedelta(days=1)
    seed: int = 7
    initial_price: Decimal = Decimal("100")
    annual_drift: float = 0.05
    annual_volatility: float = 0.20
    correlation: float = 0.25
    periods_per_year: int = 252
    regime_at: int | None = None
    regime_drift: float | None = None
    regime_volatility: float | None = None


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_EVEN)


def generate_bars(config: SyntheticConfig, clock: Callable[[], datetime]) -> list[Bar]:
    """Generate deterministic correlated GBM-like OHLCV bars.

    ``clock`` is called exactly once and must return an aware datetime. An
    optional second regime begins at ``regime_at``. Prices are rounded to cents.
    """
    start = clock()
    if start.tzinfo is None or start.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    if not config.symbols or len(set(config.symbols)) != len(config.symbols):
        raise ValueError("symbols must be non-empty and unique")
    if config.periods < 2 or config.interval <= timedelta(0):
        raise ValueError("periods must be >= 2 and interval must be positive")
    if config.initial_price <= 0 or config.annual_volatility < 0:
        raise ValueError("price must be positive and volatility non-negative")
    n = len(config.symbols)
    if n > 1 and not (-1 / (n - 1) <= config.correlation <= 1):
        raise ValueError("correlation is outside the valid equicorrelation range")
    if config.regime_at is not None and not (1 <= config.regime_at < config.periods):
        raise ValueError("regime_at must be within the generated period")

    rng = random.Random(config.seed)
    prices = {symbol: float(config.initial_price) for symbol in config.symbols}
    bars: list[Bar] = []
    # Equicorrelated normals via a small Cholesky decomposition.
    matrix = [[1.0 if i == j else config.correlation for j in range(n)] for i in range(n)]
    chol = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            subtotal = sum(chol[i][k] * chol[j][k] for k in range(j))
            if i == j:
                chol[i][j] = math.sqrt(max(matrix[i][i] - subtotal, 0.0))
            elif chol[j][j] > 0:
                chol[i][j] = (matrix[i][j] - subtotal) / chol[j][j]

    for index in range(config.periods):
        timestamp = start + config.interval * index
        independent = [rng.gauss(0, 1) for _ in range(n)]
        shocks = [sum(chol[i][j] * independent[j] for j in range(i + 1)) for i in range(n)]
        in_regime = config.regime_at is not None and index >= config.regime_at
        drift = config.regime_drift if in_regime and config.regime_drift is not None else config.annual_drift
        vol = config.regime_volatility if in_regime and config.regime_volatility is not None else config.annual_volatility
        if vol < 0:
            raise ValueError("regime volatility must be non-negative")
        step_vol = vol / math.sqrt(config.periods_per_year)
        step_drift = drift / config.periods_per_year
        for asset_index, symbol in enumerate(config.symbols):
            opening = prices[symbol]
            closing = opening * math.exp(step_drift - 0.5 * step_vol**2 + step_vol * shocks[asset_index])
            bridge = abs(rng.gauss(0, max(step_vol, 0.0001) / 3))
            high = max(opening, closing) * math.exp(bridge)
            low = min(opening, closing) * math.exp(-bridge)
            bar = Bar(timestamp, symbol, _money(opening), _money(high), _money(low),
                      _money(closing), rng.randint(1_000, 100_000))
            bars.append(bar)
            prices[symbol] = max(closing, 0.01)
    validate_bars(bars)
    return bars


def validate_bars(bars: Iterable[Bar]) -> None:
    seen: set[tuple[datetime, str]] = set()
    last: dict[str, datetime] = {}
    any_bar = False
    for bar in bars:
        any_bar = True
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            raise DataValidationError("all timestamps must be timezone-aware")
        key = (bar.timestamp, bar.symbol)
        if key in seen:
            raise DataValidationError(f"duplicate bar: {key}")
        if bar.symbol in last and bar.timestamp <= last[bar.symbol]:
            raise DataValidationError(f"bars for {bar.symbol} are not chronological")
        if not bar.symbol or bar.volume < 0 or min(bar.open, bar.high, bar.low, bar.close) <= 0:
            raise DataValidationError("symbol, prices, and volume must be valid")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close) or bar.low > bar.high:
            raise DataValidationError("OHLC relationship is impossible")
        seen.add(key)
        last[bar.symbol] = bar.timestamp
    if not any_bar:
        raise DataValidationError("at least one bar is required")
