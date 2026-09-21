# Quant Research OS

A reproducible, **simulation-only** quantitative research platform under development.

> Not a brokerage client, investment recommendation engine, or live trading system. Start with synthetic data; no paid APIs or real-money orders.

## Project brief

See [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for the full implementation mission, phased milestones, engineering constraints, and acceptance criteria.

## For Codex Cloud

Select this repository and instruct Codex:

> Read AGENTS.md and docs/PROJECT_BRIEF.md. Implement milestone A end-to-end, including deterministic synthetic data, a causally correct event-driven backtester, a working strategy, accounting, and tests. After validating A, continue with subsequent milestones if time and environment permit. Work on a feature branch and prepare a PR for review. Never merge, deploy, trade, or call paid APIs. Report exact completed scope and test results in Japanese.

Do not confuse this new project with the separate local `quant-pressure-lab` project.

## Quick start

Python 3.11+ is required. The core has no runtime dependencies.

```bash
python -m pip install -e '.[test]'
pytest
quant-research --seed 7 --periods 100 --output artifacts/demo.json
```

The generated data and simulator are research examples only. Decisions made at
close `t` execute at open `t+1`; see [Milestone A](docs/MILESTONE_A.md).

Additional offline workflows:

```bash
quant-study --output artifacts/study.json
quant-dashboard --output artifacts/dashboard.html
quant-benchmark --symbols 4 --periods 1000 --output artifacts/benchmark.json
```
