"""Bounded, reproducible command-line demonstration."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

from .backtest import run_backtest
from .data import SyntheticConfig, generate_bars
from .strategy import BuyAndHold, MovingAverageCross


def _json_default(value: object) -> str:
    if isinstance(value, (Decimal, datetime)):
        return str(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an offline synthetic backtest")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--periods", type=int, default=100)
    parser.add_argument("--strategy", choices=("buy-hold", "ma-cross"), default="ma-cross")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not 2 <= args.periods <= 100_000:
        parser.error("--periods must be between 2 and 100000")
    config = SyntheticConfig(symbols=("SYNTH_A", "SYNTH_B"), periods=args.periods, seed=args.seed)
    bars = generate_bars(config, start=datetime(2020, 1, 1, tzinfo=timezone.utc))
    strategy = BuyAndHold(10) if args.strategy == "buy-hold" else MovingAverageCross(5, 20, 10)
    result = run_backtest(bars, strategy)
    payload = {
        "assumptions": "close signal; next-bar open fill; long-only; no leverage; fixed+bps fees",
        "seed": args.seed,
        "periods": args.periods,
        "strategy": args.strategy,
        "metrics": {
            "initial_cash": result.initial_cash,
            "final_cash": result.final_cash,
            "final_equity": result.final_equity,
            "total_return": result.total_return,
            "realized_pnl": result.realized_pnl,
            "unrealized_pnl": result.unrealized_pnl,
            "total_fees": result.total_fees,
        },
        "fills": [asdict(fill) for fill in result.fills],
    }
    rendered = json.dumps(payload, default=_json_default, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
