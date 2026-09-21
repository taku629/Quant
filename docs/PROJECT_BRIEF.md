# Quant Research OS — Codex Cloud Project Brief

## Purpose and scope

Build a substantial **reproducible research and simulation-only** quantitative engineering portfolio project. It is separate from the user's existing local Quant Pressure Lab, whose source has not been transferred to this repository. Do not claim to have recovered that project.

The end-to-end workflow is:

hypothesis → data validation/generation → causal features/signals → event-driven execution simulation → portfolio accounting → risk and statistical evaluation → versioned experiment → interpretable report/dashboard.

This brief is the authority for the first coding task; refine design based on verified implementation results. Avoid empty scaffolds, generic reports, fictitious measurements, or claims of trading performance. This is not live trading software.

## Milestone A: A correct, runnable vertical slice (must finish first)

1. Create a properly packaged, typed Python research core with CLI or runnable entry point, an example, and tests. Prefer simple maintainable dependencies; avoid requiring network access or API credentials.
2. Generate deterministic synthetic one- and multi-asset OHLCV/price bars with injection of a reference clock, explicit time zones, seed-controlled randomness, configurable regime/volatility/correlation as justified, and stringent data validation.
3. Build a deterministic event-driven backtester with an explicit causal time contract. Signals generated on bar t cannot execute at the close of bar t without a documented executable next-event rule. Define orders, fills, fees, cash, positions, and exposure. Include buy-and-hold and a simple signal strategy; prove no look-ahead using intentionally adversarial tests.
4. Implement authoritative portfolio accounting including fees and realized/unrealized P&L; validate cash/positions/equity conservation with tests. Define Decimal vs floats and rounding conventions. No negative cash, shorting, or leverage unless explicitly configured and tested.
5. Demonstrate an executable end-to-end run with reproducible artifacts and a test suite. Fail loudly on invalid data, duplicate timestamps, impossible fills, and unsupported configurations.

**Exit criterion:** a fresh checkout can install the project, run tests, and execute a genuine synthetic-data backtest producing documented, reproducible metrics and trade records. Never substitute mocked financial results for engine computations.

## Milestone B: Execution realism and risk accounting

- Event contracts with deterministic ordering, identifiers, order lifecycle (pending/accepted/rejected/partially filled/filled/canceled), market and limit orders only where the supported data permits defensible fill assumptions.
- A bounded matching engine / synthetic limit order book with explicit price-time priority, bid/ask spread, insufficient liquidity and partial fills, latency and transaction-cost models. Distinguish a price-bar execution simulator from a full order book; never pretend OHLCV alone exposes order-book depth.
- Position, cash and portfolio ledgers, exposure, leverage restrictions, drawdown, turnover, realized and unrealized P&L, Sharpe/Sortino with stated sampling conventions, VaR/ES with stated assumptions and warning for tiny samples.
- Edge tests: empty books, crossed book policies, duplicate IDs, canceled order fills, out-of-order events, trade accounting, cost conservation, extreme and invalid prices.

**Exit criterion:** independently tested execution and accounting behavior; one end-to-end sample showing how transaction costs change results.

## Milestone C: Rigorous statistical research

- Chronological train/validation/test, rolling and expanding walk-forward, clear prevention of future leakage and contaminated feature computation.
- Strategy interface and representative baselines: buy/hold, momentum, mean reversion; pairs and volatility targeting only after prerequisite market data and risk logic are correct.
- Parameter sensitivity, multiple-testing warning, time-series/bootstrap uncertainty with the limitations of temporal dependence explicitly documented, genuine OOS comparisons and negative-control experiments.
- Reproducible experiments record seed, dataset provenance/hash, split, strategy config, code SHA, runtime, metrics, simulator assumptions, and outputs; provide repeatable CLI to compare experiments.

**Exit criterion:** a reproducible study with OOS comparison and an example of how in-sample attractiveness may disappear with costs or OOS data. Do not claim statistically reliable alpha from synthetic data.

## Milestone D: Usable interface and performance

- Build a small real UI only after the core is functioning, using the lowest-complexity defensible option; React/TypeScript + Python API is acceptable but not mandatory.
- UI displays **computed**, not fabricated results: equity, drawdown, fills, strategy parameters, comparable experiments, exports.
- Bounded, reproducible synthetic benchmarks that capture time, peak memory, event throughput, data volume, hardware/runtime. Profile first and optimize only confirmed bottlenecks.
- E2E tests, package smoke tests, docs and a concise technical walkthrough; record unsupported operating conditions.

**Exit criterion:** independently runnable research workflow, core tests and a small functional interface or honestly documented reason it was deferred.

## Implementation discipline

- Check initial repository SHA and status; current initial repository intentionally only contains this specification. Use a feature branch; do not merge into main.
- Work sequentially through A → B → C → D. Complete, test and commit coherent milestones; if time/budget expires, leave the last finished milestone usable and document exactly what is incomplete.
- Use standard Python testing with deterministic fixtures; CI should run without broker logins, paid APIs or external data. Prefer property tests for ledger invariants and unit tests to expose chronological leakage.
- No real orders, brokers, personal financial data, paid services, prod infrastructure, cloud deployment, secrets, or unapproved purchases. No fake benchmarks or tests. Never use third-party datasets that require auth or whose license is uncertain.
- No destructive changes to untracked user work. Never silently add a mandatory huge dependency, download multi-GB datasets, or perform unbounded benchmarks.
- PR for review is allowed if available; do not merge, deploy or enable auto-merge.
- Keep docs as accurate as implementation: design, execution assumptions, accounting conventions, research protocol, test results, benchmark methodology and limitations.
- Final report in concise **Japanese**: branch/PR, what was actually implemented, exact commands/results, reproducible demo, limitations, and next milestone.

## Starter instruction to Codex

"Read AGENTS.md and docs/PROJECT_BRIEF.md. Start with Milestone A. Complete an actual functioning, verified vertical slice before progressing, then continue B, C, D as environment and budget permit. Use a feature branch and prepare a PR. No live trading, paid APIs, or fabricated results. Do not stop at an architectural report. Finish with a Japanese summary of exact deliverables and test results."
