# Phase 2 OOS Validation — 2026-03-27_phase2_oos

Generated: 2026-03-27T22:40:13.037153+00:00

JSON: `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs/PHASE2_OOS_VALIDATION_2026-03-27_phase2_oos.json`

| Project | Scenario | Orders | Net Profit | Sharpe | Drawdown | End Equity | Fees | Output |
|---|---|---:|---:|---:|---:|---:|---:|---|
| baseline-strategy | baseline_is_2014_2018 | 130 | 0.908% | -0.942 | 3.200% | 100908.39 | $65.33 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/baseline-strategy/backtests/2026-03-27_phase2_oos/baseline_is_2014_2018` |
| baseline-strategy | baseline_oos_2019_2020 | 59 | 3.012% | -0.337 | 3.200% | 103012.21 | $27.21 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/baseline-strategy/backtests/2026-03-27_phase2_oos/baseline_oos_2019_2020` |
| regime-ensemble-alpha | regime_is_2014_2018 | 1411 | -2.348% | -0.243 | 12.300% | 97652.08 | $537.32 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_oos/regime_is_2014_2018` |
| regime-ensemble-alpha | regime_oos_2019_2020 | 528 | 1.697% | -0.114 | 17.300% | 101697.10 | $198.63 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_oos/regime_oos_2019_2020` |
| statarb-spread-engine | statarb_is_2014_2018 | 88 | -0.302% | -18.299 | 0.300% | 99697.94 | $88.00 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_oos/statarb_is_2014_2018` |
| statarb-spread-engine | statarb_oos_2019_2020 | 44 | -0.111% | -19.244 | 0.200% | 99889.25 | $44.00 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_oos/statarb_oos_2019_2020` |
| anchored-vwap-sleeve | avwap_is_2014_2018 | 2226 | -4.109% | -0.666 | 10.000% | 95890.75 | $902.61 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_oos/avwap_is_2014_2018` |
| anchored-vwap-sleeve | avwap_oos_2019_2020 | 1082 | -1.374% | -0.58 | 5.200% | 98626.23 | $381.10 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_oos/avwap_oos_2019_2020` |
| options-greeks-vix | options_is_2014 | 21 | 2.499% | 0.605 | 1.500% | 102498.55 | $21.03 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/options-greeks-vix/backtests/2026-03-27_phase2_oos/options_is_2014` |
| options-greeks-vix | options_oos_2015 | 8 | -1.003% | -2.992 | 1.000% | 98996.69 | $6.88 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/options-greeks-vix/backtests/2026-03-27_phase2_oos/options_oos_2015` |

## Notes
- IS vs OOS windows are split by calendar windows to avoid same-period tuning bias.
- These results are based on locally available LEAN sample data coverage.