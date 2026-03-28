#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT/infra"
set -a
source .env
if [[ -f .secrets ]]; then source .secrets; fi
set +a

for var in \
  ALPACA_API_KEY ALPACA_PAPER_KEY ALPACA_LIVE_KEY \
  ALPACA_API_SECRET ALPACA_PAPER_SECRET ALPACA_LIVE_SECRET \
  TRADIER_API_TOKEN TRADIER_SANDBOX_TOKEN TRADIER_LIVE_TOKEN
  do
  if [[ "${!var:-}" == REDACTED_USE_OPENCLAW_CONFIG* ]]; then
    unset "$var"
  fi
done

export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"

cd "$ROOT/services/ingestion"
python3 pull_equities_bars_stooq.py || echo "stooq bars failed"
python3 pull_tradier_greeks.py || echo "tradier greeks failed"
python3 pull_crypto_coingecko.py || echo "coingecko failed"
python3 pull_macro_fred.py || echo "fred macro failed"

echo "Phase 3.1 data lanes complete"
