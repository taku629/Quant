# Milestone A verification record

Milestone A is a complete offline vertical slice. It includes deterministic,
seeded synthetic OHLCV data, strict validation, close-signal/next-open event
execution, long-only portfolio accounting, two strategies, a CLI, deterministic
CSV/JSON artifacts, and independent tests.

Verified on Python 3.12.13 on 2026-09-21:

```text
$ python -m pytest
.........                                                                [100%]
9 passed in 0.06s

$ PYTHONPATH=src python -m quant_research.cli --seed 7 --periods 20 \
    --output /tmp/quant-demo-a
fill_count: 6
final_equity: 10017.37

$ PYTHONPATH=src python -m quant_research.cli --seed 7 --periods 20 \
    --output /tmp/quant-demo-b
$ diff -ru /tmp/quant-demo-a /tmp/quant-demo-b
(no differences)
```

The displayed equity is a simulator output for a bounded synthetic example,
not a benchmark, forecast, or claim of trading performance. See the README for
execution and accounting assumptions and unsupported behavior.
