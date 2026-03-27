# Algo System Roadmap

## Sleeves by Asset Class / Strategy

1. **Baseline Trend Sleeve**
   - File: `baseline-strategy/main.py`
   - Assets: large-cap equities (+ optional crypto)
   - Role: robust trend + stop discipline base sleeve

2. **Regime Ensemble Allocator (Enhanced)**
   - File: `regime-ensemble-alpha/main.py`
   - Assets: broad equities, defensives, optional crypto
   - Role: allocate across winners under volatility + drawdown controls

3. **StatArb Spread Engine**
   - File: `statarb-spread-engine/main.py`
   - Assets: equity pairs
   - Role: market-neutral mean reversion / spread alpha

4. **Options Greeks / Vol Sleeve (Enhanced)**
   - File: `options-greeks-vix/main.py`
   - Assets: listed options + fallback underlying
   - Role: directional options with IV/Greek controls

5. **Anchored VWAP Cross-Asset Sleeve (New)**
   - File: `anchored-vwap-sleeve/main.py`
   - Assets: index ETFs, rates/commodity ETFs, optional crypto
   - Role: AVWAP trend/reclaim entries with event anchors

## Portfolio Construction (next pass)

- Sleeve-level volatility targeting and capital bands
- Correlation-aware sleeve weighting
- Unified drawdown guard across sleeves
- Capacity checks and turnover budget by sleeve

## Testing Protocol (required before promotion)

- In-sample + out-of-sample split
- Walk-forward windows
- Parameter perturbation sensitivity
- Stress periods (COVID crash, 2022 inflation shock, crypto drawdowns)
- Costs/slippage stress (2x and 3x assumptions)
- Deflated Sharpe / overfitting checks
