# Phase 4 Platform Expansion Plan

## User goals addressed
- Strong quantitative strategy system with valid evaluation
- Execution + data ingest/transform/access tooling
- Secure VPS operations
- Move toward multi-agent operating model
- Interactive GitHub Pages frontend for strategy/portfolio/report visibility
- Token-efficient research loop (ArXiv and beyond)
- On-chain transaction tracing + Solidity analysis lane

## What is implemented now

### Quant strategy/eval lane
- Reproducible matrix, tuning, OOS, walk-forward, allocator, run ledger scripts.
- Methodology validity and data quality reports committed.

### Data tooling
- Ingestion runners + validation layer + new Phase 4 cycle runner.
- Added preflight script with auth-level DB check.

### Research tooling (token-efficient)
- `research/scripts/update_arxiv_digest.py` (no LLM usage; metadata scoring).
- ArXiv topic config and ranked digest outputs.

### Frontend
- New GitHub Pages dashboard scaffold:
  - `frontend/github-pages/index.html`
  - `frontend/github-pages/app.js`
  - `frontend/github-pages/scripts/sync_data.sh`
- GitHub Actions Pages deploy workflow.

### Blockchain lane
- Ethereum tx tracer script (RPC-driven; optional debug trace).
- Bitcoin tx flow tracer script (Blockstream API).
- Solidity static risk scanner.
- Hardhat contract introspection script.

## Immediate blockers
1. Postgres credential mismatch for ingestion user (`quant`) causing write failures.
2. Expanded remote LEAN data download blocked until QC org data terms accepted.

## Next execution order
1. Fix DB auth and re-run full ingestion cycle.
2. Accept QC terms and run expanded data pull.
3. Re-run Phase 3 matrix/walk-forward on expanded data horizon.
4. Add confidence intervals + cost stress framework.
5. Promote only sleeves that pass robustness thresholds.
