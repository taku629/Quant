# Milestone D — interface and bounded performance check

`quant-dashboard` emits a responsive, dependency-free HTML report whose equity
curve, fees, fills, and parameters are computed by the simulator. It can be
opened directly; no server or fabricated fixture data is involved.

`quant-benchmark` measures generator plus bar-simulator wall time, throughput,
and `tracemalloc` Python peak allocations. Work is hard-bounded to 20 symbols and
10,000 periods. Results depend on hardware/runtime and are descriptive, not a
performance guarantee. Unsupported: live feeds, brokers, shorts, leverage,
intraday calendars, corporate actions, and claims about real market behavior.
