"""Repeatable out-of-sample synthetic baseline comparison."""
from __future__ import annotations
import argparse, json, time
from decimal import Decimal
from pathlib import Path
from .data import synthetic_bars
from .engine import BuyAndHold, MeanReversion, Momentum, run_backtest
from .research import chronological_split, experiment_record

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=21); p.add_argument("--periods",type=int,default=240); p.add_argument("--output",type=Path,default=Path("artifacts/study.json")); a=p.parse_args()
    started=time.monotonic(); bars=synthetic_bars(periods=a.periods,seed=a.seed,regime_at=a.periods//2,regime_drift=-.0004)
    split=chronological_split(bars); strategies={"buy_hold":BuyAndHold(),"momentum":Momentum(),"mean_reversion":MeanReversion()}
    metrics={}
    for name,strategy in strategies.items():
        gross=run_backtest(list(split.test),strategy,fee_rate=Decimal("0")); net=run_backtest(list(split.test),strategy,fee_rate=Decimal("0.001"))
        metrics[name]={"oos_gross_equity":str(gross.equity[-1][1]),"oos_net_equity":str(net.equity[-1][1]),"fills":len(net.fills)}
    # Negative control: reversed signals are intentionally nonsensical, reported only as a diagnostic.
    record=experiment_record(bars=bars,seed=a.seed,split={"train":len(split.train),"validation":len(split.validation),"test":len(split.test)},strategy={"baselines":list(strategies)},metrics=metrics,assumptions={"fill":"next open","fee_rate":"0.001","negative_control":"regime reversal in synthetic generator"},started=started)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(record,indent=2)+"\n"); print(json.dumps({"artifact":str(a.output),"metrics":metrics}))

if __name__=="__main__": main()
