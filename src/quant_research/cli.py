from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .backtest import BacktestConfig, run_backtest
from .data import SyntheticConfig, generate_bars
from .strategy import BuyAndHold, Momentum


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an offline synthetic backtest")
    parser.add_argument("--output", type=Path, default=Path("artifacts/example"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--periods", type=int, default=60)
    parser.add_argument("--symbols", nargs="+", default=["AAA", "BBB"])
    parser.add_argument("--strategy", choices=("buy-hold", "momentum"), default="momentum")
    parser.add_argument("--lookback", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    start = datetime(2020, 1, 2, 16, tzinfo=timezone.utc)
    bars = generate_bars(SyntheticConfig(tuple(args.symbols), args.periods, seed=args.seed), lambda: start)
    strategy = BuyAndHold() if args.strategy == "buy-hold" else Momentum(args.lookback)
    result = run_backtest(bars, strategy, BacktestConfig(order_quantity=10))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "fills.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["order_id", "symbol", "side", "quantity", "signal_at", "filled_at", "price", "fee"])
        for fill in result.fills:
            writer.writerow([fill.order_id, fill.symbol, fill.side.value, fill.quantity,
                             fill.signal_at.isoformat(), fill.filled_at.isoformat(), fill.price, fill.fee])
    summary = {
        "assumptions": "close signal; next available bar open fill; long-only; no leverage; fee in bps",
        "seed": args.seed, "periods": args.periods, "symbols": args.symbols,
        "strategy": args.strategy, "initial_cash": str(result.initial_cash),
        "final_cash": str(result.final_cash), "final_equity": str(result.final_equity),
        "total_return": str(result.total_return), "fees": str(result.fees),
        "realized_pnl": str(result.realized_pnl), "positions": result.positions,
        "fill_count": len(result.fills),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
