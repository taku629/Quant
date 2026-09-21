"""Leakage-resistant chronological research and reproducible records."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib, json, random, subprocess, time
from typing import Sequence, TypeVar
from .data import Bar

T=TypeVar("T")
@dataclass(frozen=True)
class Split:
    train: tuple; validation: tuple; test: tuple

def chronological_split(rows: Sequence[T], train: float=.6, validation: float=.2) -> Split:
    if len(rows)<3 or train<=0 or validation<=0 or train+validation>=1: raise ValueError("invalid split")
    if any(getattr(a,"timestamp",a) >= getattr(b,"timestamp",b) for a,b in zip(rows,rows[1:])): raise ValueError("rows must be strictly chronological")
    a=int(len(rows)*train); b=a+int(len(rows)*validation)
    return Split(tuple(rows[:a]),tuple(rows[a:b]),tuple(rows[b:]))

def walk_forward(rows: Sequence[T], minimum_train: int, test_size: int, expanding: bool=True):
    if minimum_train<1 or test_size<1: raise ValueError("positive window sizes required")
    end=minimum_train
    while end+test_size<=len(rows):
        start=0 if expanding else end-minimum_train
        yield tuple(rows[start:end]),tuple(rows[end:end+test_size]); end+=test_size

def block_bootstrap_mean(values: Sequence[float], *, seed: int, block: int=5, samples: int=500) -> tuple[float,float]:
    """Percentile interval; blocks preserve only short-range dependence."""
    if not values or block<1 or samples<1: raise ValueError("values and positive settings required")
    rng=random.Random(seed); means=[]
    for _ in range(samples):
        draw=[]
        while len(draw)<len(values):
            start=rng.randrange(len(values)); draw.extend(values[(start+j)%len(values)] for j in range(block))
        means.append(sum(draw[:len(values)])/len(values))
    means.sort(); return means[int(.025*(samples-1))],means[int(.975*(samples-1))]

def dataset_hash(bars: Sequence[Bar]) -> str:
    raw="\n".join(json.dumps({**asdict(b),"timestamp":b.timestamp.isoformat()},sort_keys=True) for b in bars)
    return hashlib.sha256(raw.encode()).hexdigest()

def experiment_record(*, bars: Sequence[Bar], seed: int, split: dict, strategy: dict,
                      metrics: dict, assumptions: dict, started: float) -> dict:
    try: sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except (OSError,subprocess.CalledProcessError): sha="unknown"
    return {"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),"runtime_seconds":round(time.monotonic()-started,6),
            "seed":seed,"dataset":{"provenance":"deterministic synthetic generator","sha256":dataset_hash(bars)},
            "split":split,"strategy":strategy,"code_sha":sha,"metrics":metrics,"simulator_assumptions":assumptions,
            "warning":"Synthetic results and repeated parameter searches do not establish alpha."}
