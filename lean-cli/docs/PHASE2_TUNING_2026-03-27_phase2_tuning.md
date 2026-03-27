# Phase 2 Tuning + OOS Validation — 2026-03-27_phase2_tuning

Generated: 2026-03-27T22:53:16.206984+00:00

JSON: `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs/PHASE2_TUNING_2026-03-27_phase2_tuning.json`

## IS Grid Results

| Project | Scenario | Net Profit | Sharpe | Drawdown | Orders | End Equity | Output |
|---|---|---:|---:|---:|---:|---:|---|
| regime-ensemble-alpha | regime_cfg_a | -2.348% | -0.243 | 12.300% | 1411 | 97652.08 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_tuning/is/regime_cfg_a` |
| regime-ensemble-alpha | regime_cfg_b | 1.402% | -0.184 | 12.700% | 1417 | 101402.49 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_tuning/is/regime_cfg_b` |
| regime-ensemble-alpha | regime_cfg_c | 9.332% | 0.012 | 11.200% | 1017 | 109331.96 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_tuning/is/regime_cfg_c` |
| regime-ensemble-alpha | regime_cfg_d | -2.059% | -0.283 | 14.300% | 2269 | 97940.54 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_tuning/is/regime_cfg_d` |
| anchored-vwap-sleeve | avwap_cfg_a | -4.109% | -0.666 | 10.000% | 2226 | 95890.75 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_tuning/is/avwap_cfg_a` |
| anchored-vwap-sleeve | avwap_cfg_b | -4.267% | -0.951 | 7.500% | 2133 | 95733.31 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_tuning/is/avwap_cfg_b` |
| anchored-vwap-sleeve | avwap_cfg_c | -2.620% | -1.084 | 4.400% | 1979 | 97379.79 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_tuning/is/avwap_cfg_c` |
| anchored-vwap-sleeve | avwap_cfg_d | -5.301% | -0.861 | 9.200% | 2151 | 94698.98 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_tuning/is/avwap_cfg_d` |
| statarb-spread-engine | statarb_cfg_a | -0.302% | -18.299 | 0.300% | 88 | 99697.94 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_tuning/is/statarb_cfg_a` |
| statarb-spread-engine | statarb_cfg_b | -0.348% | -19.584 | 0.400% | 184 | 99651.62 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_tuning/is/statarb_cfg_b` |
| statarb-spread-engine | statarb_cfg_c | -0.053% | -52.945 | 0.100% | 40 | 99947.26 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_tuning/is/statarb_cfg_c` |
| statarb-spread-engine | statarb_cfg_d | -0.340% | -22.639 | 0.400% | 132 | 99659.98 | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_tuning/is/statarb_cfg_d` |

## Selected Best-by-IS and OOS Retest

| Project | Selected IS Config | IS Net | OOS Scenario | OOS Net | OOS Sharpe | OOS Drawdown | OOS Output |
|---|---|---:|---|---:|---:|---:|---|
| regime-ensemble-alpha | regime_cfg_c | 9.332% | regime_cfg_c_oos | -1.871% | -0.299 | 15.300% | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/regime-ensemble-alpha/backtests/2026-03-27_phase2_tuning/oos/regime_cfg_c_oos` |
| anchored-vwap-sleeve | avwap_cfg_c | -2.620% | avwap_cfg_c_oos | -3.749% | -1.432 | 5.100% | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/anchored-vwap-sleeve/backtests/2026-03-27_phase2_tuning/oos/avwap_cfg_c_oos` |
| statarb-spread-engine | statarb_cfg_c | -0.053% | statarb_cfg_c_oos | -0.068% | -60.114 | 0.100% | `/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/statarb-spread-engine/backtests/2026-03-27_phase2_tuning/oos/statarb_cfg_c_oos` |