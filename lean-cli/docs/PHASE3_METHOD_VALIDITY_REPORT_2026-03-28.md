# Phase 3 Methodology & Validity Report (2026-03-28)

## Objective

Provide **audit-ready** evidence for algorithm quality without inflating results:
- run reproducible backtests from scripts,
- include weak/negative sleeves (no selective hiding),
- separate matrix/tuning/walk-forward outputs,
- record known data limitations and failure modes.

## What Was Run

### 1) Phase 3 matrix (single-pass scenario suite)
- Script: `scripts/backtests/run_phase3_matrix.py`
- Report: `docs/PHASE3_BACKTEST_MATRIX_2026-03-28_phase3_matrix.md`
- JSON: `docs/PHASE3_BACKTEST_MATRIX_2026-03-28_phase3_matrix.json`

### 2) Sleeve allocator construction (from matrix results)
- Script: `scripts/backtests/build_phase3_sleeve_allocator.py`
- Report: `docs/PHASE3_SLEEVE_ALLOCATOR_2026-03-28_phase3_allocator.md`
- JSON: `docs/PHASE3_SLEEVE_ALLOCATOR_2026-03-28_phase3_allocator.json`

### 3) Walk-forward stability windows
- Script: `scripts/backtests/run_phase3_walkforward.py`
- Windows: 2014–2016, 2017–2018, 2019–2020
- Report: `docs/PHASE3_WALKFORWARD_2026-03-28_phase3_walkforward.md`
- JSON: `docs/PHASE3_WALKFORWARD_2026-03-28_phase3_walkforward.json`

### 4) Data quality audit
- Report: `docs/PHASE3_DATA_QUALITY_AUDIT.md`

## Integrity Controls Used

1. **Reproducible scripts, not ad hoc CLI-only claims**
   - Every matrix/walk-forward result generated from committed runner scripts.

2. **No positive-only selection in reports**
   - AVWAP and statarb negative performance retained and reported.

3. **Multiple windows for stability**
   - Walk-forward runs show where performance is regime-dependent.

4. **Hard artifact paths**
   - Every scenario row includes exact `backtests/...` output path.

5. **Known data constraints explicitly documented**
   - Local sample coverage ends around 2021 for key equities.
   - Remote data pull blocked until QC organization data terms accepted.

## Main Findings (Plain)

1. **Regime sleeve improved materially** in this local environment and across recent windows, but has window sensitivity (weak in 2014–2016, stronger in 2019–2020).
2. **Baseline sleeve is modest/low-vol** with mixed Sharpe; it is not fake alpha, just low edge on this data slice.
3. **Options sleeve (and fallback mode) is currently the most consistently positive** across tested windows in this environment.
4. **AVWAP sleeve remains negative across windows** (improved drawdown control, but no edge yet).
5. **Statarb sleeve remains near-flat to negative after costs** (likely insufficient spread edge under current assumptions).

## Important Caveats

1. **Local data limitation**
   - Results are valid for available local dataset, but not yet “institutional complete” for full-history confidence.

2. **QC terms gate for remote data expansion**
   - `--download-data` run fails until QC organization data terms are accepted.

3. **Sharpe reliability on low-trade sleeves**
   - Very low order counts can produce unstable/extreme Sharpe values (especially statarb).

4. **Daily-bar model limitations**
   - Stop/entry sequencing and gap behavior can diverge from intraday/live execution.

## Replication Commands

From `lean-cli/`:

```bash
python3 scripts/backtests/run_phase3_matrix.py
python3 scripts/backtests/build_phase3_sleeve_allocator.py
python3 scripts/backtests/run_phase3_walkforward.py
```

## What Should Be Challenged (by external reviewers)

If reviewing with Claude/ChatGPT or other peers, challenge these explicitly:
- regime sleeve robustness under different transaction-cost assumptions,
- options sleeve behavior under alternative option-chain quality filters,
- whether AVWAP sleeve needs structural redesign instead of parameter tuning,
- statarb viability after stricter cost and borrow assumptions,
- overfitting risk if selecting only best windows.

## Next Actions (Phase 4 candidate)

1. Accept QC data terms and run expanded data pulls.
2. Re-run matrix + walk-forward on expanded dataset.
3. Add cost-stress multipliers and bootstrapped confidence intervals.
4. Keep AVWAP/statarb at zero allocation until they clear minimum robustness thresholds.
