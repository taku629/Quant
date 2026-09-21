# Quant Research OS

A reproducible, **simulation-only** quantitative research platform. Milestone A
provides a typed, deterministic vertical slice from synthetic OHLCV generation
through causal execution and portfolio accounting to reproducible artifacts.

> Not a brokerage client, investment recommendation engine, or live trading system. Start with synthetic data; no paid APIs or real-money orders.

## Project brief

See [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for the full implementation mission, phased milestones, engineering constraints, and acceptance criteria.

## For Codex Cloud

Select this repository and instruct Codex:

> Read AGENTS.md and docs/PROJECT_BRIEF.md. Implement milestone A end-to-end, including deterministic synthetic data, a causally correct event-driven backtester, a working strategy, accounting, and tests. After validating A, continue with subsequent milestones if time and environment permit. Work on a feature branch and prepare a PR for review. Never merge, deploy, trade, or call paid APIs. Report exact completed scope and test results in Japanese.

Do not confuse this new project with the separate local `quant-pressure-lab` project.

## Install and verify

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
quant-research --seed 7 --periods 60 --output artifacts/example
```

The command writes computed `summary.json` and `fills.csv` files. Repeating it
with the same arguments produces identical contents.

## Simulation contract

* The injected clock supplies the first timezone-aware timestamp; all randomness
  comes from a local, explicit seed. Synthetic assets use correlated Gaussian
  shocks and optional drift/volatility regime changes.
* A strategy sees a bar only after pending orders have executed. A signal made
  from close at time *t* becomes a market order filled at the next available
  bar's open for that symbol—never at the already observed close.
* Prices, cash, fees, and reported P&L use `Decimal`; generated prices and cash
  movements use cents with round-half-even. Quantity is an integer. The engine
  is long-only, unlevered, and rejects unaffordable fills rather than silently
  resizing them. Fees are charged on notional at the configured basis points.
* Equity is authoritative cash plus latest-close holdings. Average cost includes
  buy fees; realized P&L deducts both entry cost and sell fees. Pending orders at
  the end of data remain unfilled and do not affect accounting.

## Scope and limitations

This is a bar-level research simulator, not an order-book model. It assumes the
configured quantity can fill completely at the next open; volume, spread,
slippage, partial fills, dividends, splits, taxes, shorts, and leverage are not
modeled. Synthetic results are demonstrations, not evidence of investment edge
or recommendations. Milestones B–D remain future work.
