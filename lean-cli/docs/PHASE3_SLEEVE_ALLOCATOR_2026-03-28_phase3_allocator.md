# Phase 3 Sleeve Allocator — 2026-03-28_phase3_allocator

Generated: 2026-03-28T03:17:00.674823+00:00

Source matrix: `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs/PHASE3_BACKTEST_MATRIX_2026-03-28_phase3_matrix.json`
JSON artifact: `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs/PHASE3_SLEEVE_ALLOCATOR_2026-03-28_phase3_allocator.json`

| Sleeve | Selected Scenario | Net Profit | Sharpe | Drawdown | Score | Suggested Weight |
|---|---|---:|---:|---:|---:|---:|
| baseline-strategy | baseline_phase3_oos | 3.019% | -0.325 | 3.200% | 0.6368 | 0.1270 |
| regime-ensemble-alpha | regime_phase3_core | 24.228% | 0.185 | 9.500% | 3.0221 | 0.6028 |
| anchored-vwap-sleeve | avwap_phase3_conservative | -1.582% | -1.034 | 6.100% | 0.0000 | 0.0000 |
| statarb-spread-engine | statarb_phase3_oos | -0.090% | -29.083 | 0.100% | 0.0000 | 0.0000 |
| options-greeks-vix | options_phase3_fallback | 3.170% | 0.154 | 2.700% | 1.3549 | 0.2702 |

## Allocation Rule
- Zero weight if net profit <= 0 or drawdown > 20%.
- Otherwise score = (net% * (1 + sharpe_clamped)) / drawdown%.
- Normalize positive scores to 100% total.