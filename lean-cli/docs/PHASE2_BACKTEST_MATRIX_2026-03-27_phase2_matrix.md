# Phase 2 Backtest Matrix — 2026-03-27_phase2_matrix

Generated: 2026-03-27T22:33:21.563913+00:00

JSON artifact: `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs/PHASE2_BACKTEST_MATRIX_2026-03-27_phase2_matrix.json`

| Project | Scenario | Orders | Net Profit | Sharpe | Drawdown | End Equity | Fees | Data Fail % | Output |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| baseline-strategy | baseline_core | 86 | 2.698% | -0.729 | 3.200% | 102697.63 | $37.06 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/baseline-strategy/backtests/2026-03-27_phase2_matrix/baseline_core` |
| baseline-strategy | baseline_defensive | 86 | 1.958% | -1.093 | 2.500% | 101958.44 | $29.83 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/baseline-strategy/backtests/2026-03-27_phase2_matrix/baseline_defensive` |
| baseline-strategy | baseline_aggressive | 86 | 3.651% | -0.422 | 4.700% | 103650.96 | $53.75 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/baseline-strategy/backtests/2026-03-27_phase2_matrix/baseline_aggressive` |
| regime-ensemble-alpha | regime_core | 750 | -9.415% | -0.58 | 23.400% | 90584.80 | $276.63 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_matrix/regime_core` |
| regime-ensemble-alpha | regime_low_turnover | 490 | -14.090% | -0.625 | 27.200% | 85909.70 | $171.92 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_matrix/regime_low_turnover` |
| regime-ensemble-alpha | regime_risk_tight | 547 | -9.840% | -0.631 | 23.800% | 90159.57 | $199.35 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_matrix/regime_risk_tight` |
| statarb-spread-engine | statarb_core | 56 | -0.131% | -22.486 | 0.200% | 99869.14 | $56.00 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_matrix/statarb_core` |
| statarb-spread-engine | statarb_conservative | 36 | -0.168% | -36.97 | 0.200% | 99831.58 | $36.00 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_matrix/statarb_conservative` |
| statarb-spread-engine | statarb_active | 120 | -0.300% | -10.308 | 0.400% | 99700.33 | $120.00 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_matrix/statarb_active` |
| anchored-vwap-sleeve | avwap_core | 1650 | -3.183% | -0.631 | 8.300% | 96816.70 | $592.55 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_matrix/avwap_core` |
| anchored-vwap-sleeve | avwap_defensive | 1569 | -3.889% | -0.951 | 7.300% | 96110.88 | $457.51 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_matrix/avwap_defensive` |
| anchored-vwap-sleeve | avwap_aggressive | 1731 | -2.209% | -0.446 | 9.000% | 97790.51 | $746.83 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_matrix/avwap_aggressive` |
| options-greeks-vix | options_core | 21 | 2.776% | 0.099 | 2.600% | 102776.15 | $21.03 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/options-greeks-vix/backtests/2026-03-27_phase2_matrix/options_core` |
| options-greeks-vix | options_tighter_greeks | 21 | 2.776% | 0.099 | 2.600% | 102776.15 | $21.03 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/options-greeks-vix/backtests/2026-03-27_phase2_matrix/options_tighter_greeks` |
| options-greeks-vix | options_fallback_only | 0 | 0% | 0 | 0% | 100000 | $0.00 | n/a | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/options-greeks-vix/backtests/2026-03-27_phase2_matrix/options_fallback_only` |

## Sanity Checks

- ⚠️ `options-greeks-vix:options_fallback_only` had zero orders