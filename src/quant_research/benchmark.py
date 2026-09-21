"""Bounded synthetic benchmark with wall time and Python peak allocations."""
from __future__ import annotations
import argparse,json,platform,time,tracemalloc
from pathlib import Path
from .data import synthetic_bars
from .engine import Momentum,run_backtest
def measure(symbols:int=4,periods:int=1000,seed:int=7)->dict:
    if not 1<=symbols<=20 or not 10<=periods<=10000: raise ValueError("benchmark bounds exceeded")
    tracemalloc.start(); start=time.perf_counter(); bars=synthetic_bars(symbols=tuple(f"S{i}" for i in range(symbols)),periods=periods,seed=seed); result=run_backtest(bars,Momentum()); elapsed=time.perf_counter()-start; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {"seed":seed,"symbols":symbols,"periods":periods,"events":len(bars),"fills":len(result.fills),"wall_seconds":elapsed,"events_per_second":len(bars)/elapsed,"python_peak_bytes":peak,"python":platform.python_version(),"platform":platform.platform(),"scope":"generator + bar simulator; excludes install/startup"}
def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--symbols",type=int,default=4);p.add_argument("--periods",type=int,default=1000);p.add_argument("--seed",type=int,default=7);p.add_argument("--output",type=Path,default=Path("artifacts/benchmark.json"));a=p.parse_args(); data=measure(a.symbols,a.periods,a.seed);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+"\n");print(json.dumps(data))
if __name__=="__main__":main()
