"""Deterministic research and execution simulation (never live trading)."""

from .backtest import BacktestResult, run_backtest
from .data import SyntheticConfig, generate_bars, validate_bars
from .strategy import BuyAndHold, MovingAverageCross

__all__ = [
    "BacktestResult",
    "BuyAndHold",
    "MovingAverageCross",
    "SyntheticConfig",
    "generate_bars",
    "run_backtest",
    "validate_bars",
]
