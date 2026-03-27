# Reading Queue (Implementation-First)

## Tier 1 — Immediate build impact (read first)

1. Almgren & Chriss (2000) — execution cost model baseline
2. VWAP Execution as an Optimal Strategy (arXiv:1408.6118)
3. Jegadeesh & Titman (1993) — cross-sectional momentum
4. Moskowitz/Ooi/Pedersen (2012) — time-series momentum
5. Moreira & Muir (2017) — volatility-managed portfolios
6. Gatev/Goetzmann/Rouwenhorst (2006) — pairs baseline
7. Avellaneda & Lee (2010) — industrial statarb framing
8. Gatheral SVI (2004) — no-arb surface parameterization
9. Heston (1993) — stochastic vol baseline
10. Christoffersen & Jacobs (2004) — objective function matters in option model ranking
11. Probability of Backtest Overfitting + Deflated Sharpe Ratio

## Tier 2 — derivative depth + 0DTE

12. Dupire (1994) — local vol
13. Hagan et al. SABR (2002)
14. Differential ML for 0DTE options (arXiv:2603.07600)
15. Cont & Tankov — jumps and tail behavior
16. Deep Hedging (Buehler et al.)

## Tier 3 — extension and scale

17. Hansen SPA / White Reality Check (model selection discipline)
18. ML Statarb surveys and RL pair-trading papers (only after strong linear baseline)
19. Crypto factor and microstructure empirical literature

## Build Mapping

- **Anchored VWAP sleeve:** #1, #2, #3, #4, #5
- **Regime ensemble allocator:** #3, #4, #5, #11, #17
- **Statarb spread engine:** #6, #7, #17, #18
- **Options/Greeks engine:** #8, #9, #10, #12, #14, #15, #16
