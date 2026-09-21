from __future__ import annotations
import argparse
import json
from decimal import Decimal
from pathlib import Path
from .data import synthetic_bars
from .engine import Momentum, run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline synthetic backtest")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--periods", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("artifacts/demo.json"))
    args = parser.parse_args()
    bars = synthetic_bars(symbols=("SYN_A", "SYN_B"), periods=args.periods, seed=args.seed)
    result = run_backtest(bars, Momentum(), fee_rate=Decimal("0.001"))
    payload = {"seed": args.seed, "periods": args.periods, "assumption": "signal close t; fill open t+1",
               "final_equity": str(result.equity[-1][1]), "fees": str(result.portfolio.fees),
               "fills": [{"timestamp": f.timestamp.isoformat(), "symbol": f.symbol, "quantity": f.quantity,
                           "price": str(f.price), "fee": str(f.fee), "signal_timestamp": f.signal_timestamp.isoformat()}
                          for f in result.fills]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"artifact": str(args.output), "final_equity": payload["final_equity"], "fills": len(result.fills)}))


if __name__ == "__main__":
    main()
