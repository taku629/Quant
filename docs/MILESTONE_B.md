# Milestone B — execution and risk

`OrderBook` is a bounded synthetic price-time-priority matcher with explicit
liquidity, partial fills, cancellation, rejection and duplicate-ID protection.
It is deliberately distinct from the OHLCV simulator and makes no depth claims.
Risk statistics use simple daily returns, zero risk-free rate, population
volatility, 252-period annualization, historical VaR/ES, and tiny-sample warnings.
