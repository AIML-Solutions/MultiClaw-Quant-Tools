# VPS Hardening & Operations Checklist

## Current status (2026-03-28)

### OpenClaw
- Gateway running and reachable locally.
- Phase 3 fallback-chain hardening applied (small-model fallback removed).
- Remaining warning: reverse proxy trusted headers not configured (safe if local-only UI).

### Quant stack
- Strategy matrix / walk-forward / allocator pipelines operational.
- Ingestion lane scripts now use dynamic repo-root resolution (portable across paths).
- Phase 4 cycle runner available: `services/ingestion/run_phase4_cycle.sh`.

### Blocking issue
- Postgres auth mismatch for ingestion user `quant`.
- Symptom from preflight:
  - `postgres_tcp_5432`: OK
  - `postgres_auth_query`: FAIL (password authentication failed)

## Immediate fix sequence

1. Validate DB credentials in `infra/.env` + `.secrets`.
2. Test manually:
   ```bash
   PGPASSWORD='<password>' psql -h 127.0.0.1 -U quant -d quant -c 'select 1;'
   ```
3. If invalid, rotate/reset user password in Postgres and update secrets source.
4. Re-run preflight:
   ```bash
   bash services/ingestion/run_phase4_cycle.sh
   ```

## Security controls to enforce

- OS patching cadence (weekly, unattended upgrades where appropriate)
- UFW/NFT firewall: only required ports open
- SSH hardening: key-only auth, fail2ban, no root login
- Secrets policy: no plaintext secrets in repo; use env/secrets files with strict perms
- Backups: encrypted daily snapshots for DB + strategy artifacts
- Monitoring: basic process and disk alerts

## Operational cadence

- Daily: run Phase 4 cycle + inspect preflight + ingestion results
- 2-3x weekly: backtest matrix refresh
- Weekly: walk-forward + allocator refresh
- Weekly: `openclaw security audit --deep`
- Monthly: vulnerability scan + dependency upgrades
