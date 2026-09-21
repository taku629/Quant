# Milestone A — verified vertical slice

The package generates seed-controlled, timezone-aware synthetic OHLCV and runs a
long-only event simulator. A decision observes bars only through close `t`; it is
eligible at open `t+1`. Prices use floats at the data boundary, while authoritative
cash and fees use `Decimal`, rounded half-even to cents. Fills that would create
negative cash are rejected. OHLCV is synthetic and results are not evidence of alpha.

```bash
python -m pip install -e '.[test]'
pytest
quant-research --seed 7 --periods 100 --output artifacts/demo.json
```
