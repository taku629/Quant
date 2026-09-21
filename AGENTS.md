# Codex instructions for Quant Research OS

Read `docs/PROJECT_BRIEF.md` before modifying code. This is a fresh research/simulation project, not a copy of the separate local Quant Pressure Lab.

Build **real, tested functionality**, not a skeleton. Prioritize a complete Milestone A vertical slice before B/C/D. Use a feature branch, make focused commits, prepare a pull request for review where supported; never merge or deploy. Check the current repository state and any other agent's edits before starting.

No broker connections, real-money trading, investment recommendations, personal account data, live payments, paid APIs, production credentials, large unapproved downloads, or destructive Git operations. Do not fabricate execution results, benchmarks, return figures, or passing tests.

Enforce deterministic seeds, causality/no look-ahead, explicit execution/fill assumptions, portfolio accounting invariants, chronological validation, reproducibility, and independent automated tests. Prefer offline synthetic data. Keep sample/benchmark runs bounded.

At each milestone: implement, test, document exact commands/results, commit if verified, then proceed. If execution stops early, leave a working vertical slice and an honest status report.

Finish with a concise Japanese report suitable for viewing on a smartphone.
