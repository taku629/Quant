# Milestone C — chronological research

Chronological holdouts and rolling/expanding walk-forward windows enforce strict
time ordering. Momentum, mean-reversion, and buy/hold baselines share the causal
strategy interface. Seeded circular block bootstrap intervals retain limited
short-range dependence but are not proof of significance. Experiment records
include synthetic provenance/hash, seed, split/config, Git SHA, runtime, metrics,
and execution assumptions. Parameter searches require a multiple-testing warning;
synthetic in-sample results are never investment evidence.

Run `quant-study --seed 21 --periods 240 --output artifacts/study.json` for a
repeatable OOS baseline/cost comparison over a deliberately reversed synthetic regime.
