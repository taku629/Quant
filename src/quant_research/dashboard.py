"""Dependency-free static report UI generated solely from computed results."""
from __future__ import annotations
import argparse, html, json
from decimal import Decimal
from pathlib import Path
from .data import synthetic_bars
from .engine import Momentum, run_backtest

def render(seed: int=7, periods: int=100) -> str:
    result=run_backtest(synthetic_bars(periods=periods,seed=seed),Momentum())
    values=[float(v) for _,v in result.equity]; lo,hi=min(values),max(values); width,height=700,220
    points=" ".join(f"{i*width/max(1,len(values)-1):.1f},{height-(v-lo)*height/max(1e-9,hi-lo):.1f}" for i,v in enumerate(values))
    rows="".join(f"<tr><td>{html.escape(f.timestamp.isoformat())}</td><td>{html.escape(f.symbol)}</td><td>{f.quantity}</td><td>{f.price}</td><td>{f.fee}</td></tr>" for f in result.fills)
    return f"""<!doctype html><html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Quant Research OS</title><style>body{{font:16px system-ui;max-width:900px;margin:auto;padding:1rem;background:#0b1220;color:#e5e7eb}}.cards{{display:flex;gap:1rem;flex-wrap:wrap}}.card{{background:#172033;padding:1rem;border-radius:8px}}svg{{width:100%;background:#fff}}table{{width:100%;border-collapse:collapse}}td,th{{padding:.4rem;border-bottom:1px solid #334155;text-align:right}}td:first-child,th:first-child{{text-align:left}}</style><h1>Quant Research OS</h1><p>Simulation only · signal close t / fill open t+1</p><div class=cards><div class=card>Final equity<br><b>{result.equity[-1][1]}</b></div><div class=card>Fees<br><b>{result.portfolio.fees}</b></div><div class=card>Fills<br><b>{len(result.fills)}</b></div><div class=card>Seed<br><b>{seed}</b></div></div><h2>Computed equity</h2><svg viewBox='0 0 {width} {height}' aria-label='equity curve'><polyline fill=none stroke='#2563eb' stroke-width=3 points='{points}'/></svg><h2>Fills</h2><table><thead><tr><th>Time</th><th>Symbol</th><th>Qty</th><th>Price</th><th>Fee</th></tr></thead><tbody>{rows}</tbody></table></html>"""

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=7); p.add_argument("--periods",type=int,default=100); p.add_argument("--output",type=Path,default=Path("artifacts/dashboard.html")); a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(render(a.seed,a.periods)); print(json.dumps({"artifact":str(a.output),"seed":a.seed,"periods":a.periods}))
if __name__=="__main__": main()
