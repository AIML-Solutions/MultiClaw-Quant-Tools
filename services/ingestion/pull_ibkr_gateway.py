#!/usr/bin/env python3
"""
Fetch IBKR account, positions, and orders from the local Client Portal gateway;
write a snapshot and invoke ingest_broker_snapshot.py to load into the quant database.

Paper vs live is determined by the account the gateway is logged into (not by this script).
Requires IBEAM_GATEWAY_BASE_URL (default https://localhost:5001) and a running, authenticated gateway.
"""
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = os.getenv("IBEAM_GATEWAY_BASE_URL", "https://localhost:5001").rstrip("/")
# Local gateway typically uses a self-signed cert; set IBEAM_VERIFY_SSL=true when using a verified host.
VERIFY_SSL = os.getenv("IBEAM_VERIFY_SSL", "false").lower() in ("1", "true", "yes")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quant:quant_dev_change_me@127.0.0.1:5432/quant")

SCRIPT_DIR = Path(__file__).resolve().parent


def main():
    session = requests.Session()
    auth_resp = session.get(
        f"{BASE_URL}/v1/api/iserver/auth/status",
        verify=VERIFY_SSL,
        timeout=15,
    )
    if auth_resp.status_code != 200:
        raise SystemExit(f"IBKR auth status HTTP {auth_resp.status_code}")
    auth_status = auth_resp.json()
    if not auth_status.get("authenticated"):
        raise SystemExit("IBKR gateway not authenticated")

    accounts_resp = session.get(
        f"{BASE_URL}/v1/api/portfolio/accounts",
        verify=VERIFY_SSL,
        timeout=20,
    )
    accounts = accounts_resp.json() if accounts_resp.ok else []
    if not accounts:
        raise SystemExit("No IBKR accounts returned")
    account_id = accounts[0].get("accountId") or accounts[0].get("id")

    positions_resp = session.get(
        f"{BASE_URL}/v1/api/portfolio/{account_id}/positions/0",
        verify=VERIFY_SSL,
        timeout=25,
    )
    positions = positions_resp.json() if positions_resp.ok else []
    if not isinstance(positions, list):
        positions = []

    orders_resp = session.get(
        f"{BASE_URL}/v1/api/iserver/account/orders",
        params={"force": "false"},
        verify=VERIFY_SSL,
        timeout=25,
    )
    orders_data = orders_resp.json() if orders_resp.ok else {}
    order_list = orders_data.get("orders") or []
    if not isinstance(order_list, list):
        order_list = []

    snapshot = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "account": {
            "status": "AUTHENTICATED",
            "base_currency": "USD",
            "account_id": account_id,
            "auth": auth_status,
        },
        "positions": positions,
        "orders": order_list,
    }

    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(snapshot, f, indent=2)
            tmp = f.name

        ingest_py = SCRIPT_DIR / "ingest_broker_snapshot.py"
        cmd = [
            "python3",
            str(ingest_py),
            "--provider", "ibkr",
            "--account-id", account_id,
            "--mode", "live",
            "--snapshot", tmp,
            "--db-url", DATABASE_URL,
        ]
        subprocess.run(cmd, check=True)
        print(f"IBKR gateway pull+ingest complete (account={account_id}, positions={len(positions)}, orders={len(order_list)})")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


if __name__ == "__main__":
    main()
