# Phase 3 Data Quality Audit

Generated: 2026-03-28T01:59:59.179460Z

## Local Equity Daily Coverage

| Symbol | First Date | Last Date | Bars |
|---|---:|---:|---:|
| SPY | 19980102 00:00 | 20210331 00:00 | 5849 |
| QQQ | 19990310 00:00 | 20210331 00:00 | 3964 |
| IWM | 20000526 00:00 | 20210331 00:00 | 5244 |
| EEM | 19980106 00:00 | 20210331 00:00 | 5245 |
| AAPL | 19980102 00:00 | 20210331 00:00 | 5849 |
| BAC | 19980102 00:00 | 20210331 00:00 | 5849 |
| IBM | 19980102 00:00 | 20210331 00:00 | 5849 |
| GOOG | 20040819 00:00 | 20210331 00:00 | 4183 |
| USO | 19980102 00:00 | 20210331 00:00 | 3910 |
| BNO | 19980102 00:00 | 20210331 00:00 | 3827 |

## Local Options Data
- Option data files found: **92**

## Local Crypto Daily Coverage (Coinbase)

| File | First Date | Last Date | Bars |
|---|---:|---:|---:|
| btcusd_trade.zip | 20141201 00:00 | 20180813 00:00 | 1318 |

## Remote Data Expansion Probe
- `lean backtest --download-data --data-purchase-limit 0` probe failed before fetch due terms gate on API Data Provider.
- Required action: accept data terms at QuantConnect organization terms URL shown by LEAN error before remote pulls can proceed.