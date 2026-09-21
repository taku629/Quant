"""Reproducible, simulation-only quantitative research primitives."""

from .backtest import BacktestConfig, BacktestResult, run_backtest
from .data import SyntheticConfig, generate_bars, validate_bars
from .strategy import BuyAndHold, Momentum

__all__ = [
    "BacktestConfig", "BacktestResult", "BuyAndHold", "Momentum",
    "SyntheticConfig", "generate_bars", "run_backtest", "validate_bars",
]
