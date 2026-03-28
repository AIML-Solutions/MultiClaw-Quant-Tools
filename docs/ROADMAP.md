# MultiClaw Quant Roadmap

## Phase 1 — Proven baseline (complete)
- [x] LEAN setup and authenticated execution
- [x] Baseline backtest run and artifact generation
- [x] Postgres + Hasura + Qdrant stack online
- [x] Backtest summary ingestion + GraphQL query validation

## Phase 2 — Data productization (in progress)
- [x] Multi-source ingestion skeleton (equities/options/crypto/macro)
- [x] Pydantic validation layer for ingest payloads
- [x] Replayable ingestion shell runners
- [ ] Continuous, monitored quality checks + alerting
- [ ] Idempotent replay/recovery with quarantine reprocess UI

## Phase 3 — Strategy intelligence (in progress)
- [x] Sleeve set: baseline/regime/statarb/options/anchored-vwap
- [x] Reproducible matrix scripts
- [x] Walk-forward stability scripts
- [x] Methodology validity report + caveats
- [ ] Cost-stress confidence intervals and bootstrap significance
- [ ] Expanded data horizon (post-2021, pending QC terms acceptance)

## Phase 4 — Production quant platform hardening (active)
- [x] Org GitHub governance baseline (branch protection + CI hygiene)
- [x] Multi-repo health audit tooling
- [x] Phase 3 infra hardening in OpenClaw fallback model chain
- [ ] VPS hardening scorecard automation (OS patching/firewall/least-privilege)
- [ ] Unified run ledger: backtest + paper-trade + improvement lineage graph
- [ ] Multi-agent orchestration playbook and role contracts

## Phase 5 — Execution & observability product
- [ ] GitHub Pages interactive dashboard for:
  - strategy roster + code links
  - latest matrix/walk-forward metrics
  - paper portfolio snapshots
  - run logs and analysis changelog
- [ ] RPC/GraphQL endpoints powering dashboard with signed read-only access
- [ ] Nightly/weekly report generation with provenance hashes

## Phase 6 — On-chain alpha lane (BTC/ETH)
- [ ] Ethereum transaction tracing toolkit (receipt/log/call-trace support)
- [ ] Bitcoin UTXO flow tracing toolkit
- [ ] Solidity static risk scanner + Hardhat introspection workflow
- [ ] Event-driven on-chain feature extraction for quant models

## Phase 7 — Token-efficient research machine
- [ ] ArXiv/SSRN digest updater with topic scoring and dedup
- [ ] Minimal-token abstract triage and backlog ranking
- [ ] Strategy-to-paper mapping and evidence matrix
- [ ] Auto-generated “research changed what in code?” traceability notes
