# Quant Research OS

A reproducible, **simulation-only** quantitative research core. It does not connect to
brokers, place real orders, or provide investment recommendations.

## Milestone A vertical slice

- Seeded one- or multi-asset synthetic OHLCV with timezone-aware timestamps,
  an injectable clock, a configurable non-negative equicorrelation factor, and strict
  validation.
- Event-driven, long-only backtesting. A signal observes the close of bar `t`; its market
  order can execute only at the open of the next bar for that symbol.
- Decimal cash accounting (banker's rounding to cents), integer quantities, fixed and
  basis-point fees, average-cost realized/unrealized P&L, and cash/position safeguards.
- Buy-and-hold and moving-average-cross examples, JSON artifacts, and adversarial tests.

## Install, test, and run

Python 3.11 or newer is required. No network, credentials, or external market data are
needed after installing the package and pytest.

```bash
python -m pip install -e '.[test]'
python -m pytest
quant-research --seed 7 --periods 100 --strategy ma-cross --output result.json
```

The CLI run is bounded to 100,000 periods and emits computed metrics and every fill. The
same arguments produce byte-identical JSON. Synthetic results demonstrate software
behavior only; they are not evidence of investable performance.

## Execution and accounting contract

At each timestamp the engine (1) fills orders submitted on an earlier bar at the current
open, (2) exposes current closes to the strategy and queues target-position changes, then
(3) marks positions at current closes. There are no close-on-signal fills. Orders beyond
available cash and sells beyond holdings are rejected; borrowing, shorting, leverage,
partial fills, slippage, and volume constraints are not supported in Milestone A. A final
bar's queued order is returned in `unfilled_orders` rather than silently filled.

Prices, cash, fees, and reported P&L use `Decimal`, rounded half-even to cents at
transaction boundaries. Per-unit average cost retains sub-cent precision so total cost
basis is conserved. Synthetic stochastic calculations use seeded binary floats
and are quantized to cents when bars are created. Equity is always cash plus close-marked
holdings. Buy fees enter cost basis; sell fees enter realized P&L.

## Current limitations / next milestone

This is a bar simulator, not an order book. Market orders fill fully at the next open when
cash/inventory permits. It has no spread, liquidity, latency, limit orders, corporate
actions, risk-adjusted statistics, or train/validation/test research protocol. Those are
Milestones B and C in [the project brief](docs/PROJECT_BRIEF.md), and should be added only
with explicit assumptions and independent tests.
