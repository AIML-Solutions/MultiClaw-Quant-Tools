# MultiClaw Quant Tools

[![Quant Quality Gate](https://github.com/AIML-Solutions/MultiClaw-quant-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/AIML-Solutions/MultiClaw-quant-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e.svg)](LICENSE)

Quant engineering stack for paper-trading strategy research, execution-model realism, and Claw-native automation workflows.

## Current focus (last 3 months)

- Regime-specialist execution rollouts across strategy sleeves
- Nonlinear market-impact and liquidity-aware sizing controls
- Validation discipline upgrades (walk-forward and stress-first workflow)
- Claw-integrated repo operations and automation cadence

## What this repository does

- Runs LEAN strategy research and backtest workflows
- Maintains options/greeks and statarb strategy implementations
- Provides ingestion + query surfaces (GraphQL/JSON-RPC scaffolds)
- Supports operational docs and runbooks for repeatable quant workflows

## Strategy lanes

- `lean-cli/baseline-strategy/` — trend sleeve foundation
- `lean-cli/regime-ensemble-alpha/` — allocator with regime controls
- `lean-cli/statarb-spread-engine/` — spread mean-reversion engine
- `lean-cli/options-greeks-vix/` — options/volatility execution lane
- `lean-cli/anchored-vwap-sleeve/` — cross-asset AVWAP sleeve

## Core docs

- `lean-cli/ALGO_SYSTEM_ROADMAP.md`
- `docs/architecture.md`
- `docs/runbook.md`
- `docs/graphql-examples.md`
- `docs/ROADMAP.md`

## Quick start

```bash
# LEAN auth
lean login
lean whoami

# infra bootstrap
cd infra
cp .env.example .env
docker compose up -d

# run a local smoke backtest
cd ../lean-cli
lean backtest "baseline-strategy" --no-update
```

## Standards

Every strategy change should pass this gate:
1. design rationale
2. code implementation
3. structural validation
4. stress-aware performance checks

## Security & usage

- Paper-trading/research use only
- Never commit secrets
- Review external integrations before enabling write permissions

## License

MIT — see `LICENSE`.
