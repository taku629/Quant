"""Risk statistics with explicit population/daily conventions."""
from __future__ import annotations
import math

def returns(equity: list[float]) -> list[float]:
    if any(x <= 0 or not math.isfinite(x) for x in equity): raise ValueError("equity must be positive and finite")
    return [b/a-1 for a,b in zip(equity, equity[1:])]

def max_drawdown(equity: list[float]) -> float:
    if not equity: return 0.0
    peak = equity[0]; worst = 0.0
    for value in equity:
        peak = max(peak, value); worst = min(worst, value/peak-1)
    return worst

def annualized_ratios(values: list[float], periods: int = 252) -> dict[str, float | str]:
    """Population-volatility Sharpe/Sortino, zero risk-free rate."""
    if len(values) < 2: return {"sharpe": 0.0, "sortino": 0.0, "warning": "tiny sample"}
    mean = sum(values)/len(values); variance = sum((x-mean)**2 for x in values)/len(values)
    downside = sum(min(x, 0)**2 for x in values)/len(values)
    return {"sharpe": mean/math.sqrt(variance)*math.sqrt(periods) if variance else 0.0,
            "sortino": mean/math.sqrt(downside)*math.sqrt(periods) if downside else 0.0,
            **({"warning": "tiny sample"} if len(values) < 30 else {})}

def historical_var_es(values: list[float], alpha: float = .05) -> tuple[float, float, str | None]:
    if not values or not 0 < alpha < 1: raise ValueError("returns and alpha required")
    ordered = sorted(values); count = max(1, math.ceil(len(values)*alpha)); tail = ordered[:count]
    return -tail[-1], -sum(tail)/len(tail), "tiny sample" if len(values) < 100 else None
