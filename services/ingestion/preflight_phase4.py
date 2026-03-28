#!/usr/bin/env python3
"""
Phase 4 preflight checks for ingestion stack readiness.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def check_tcp(host: str, port: int, timeout: float = 1.5) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def main():
    checks = []

    db_url = os.getenv("DATABASE_URL", "")
    checks.append(Check("DATABASE_URL_set", bool(db_url), "set" if db_url else "missing"))

    postgres_up = check_tcp("127.0.0.1", 5432)
    checks.append(Check("postgres_tcp_5432", postgres_up, "reachable" if postgres_up else "not reachable"))

    db_auth_ok = False
    db_auth_detail = "skipped"
    if db_url:
        try:
            import psycopg  # type: ignore

            with psycopg.connect(db_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("select 1")
                    cur.fetchone()
            db_auth_ok = True
            db_auth_detail = "auth+query ok"
        except Exception as exc:
            db_auth_ok = False
            db_auth_detail = str(exc).splitlines()[-1][:220]
    checks.append(Check("postgres_auth_query", db_auth_ok, db_auth_detail))

    tradier = any(os.getenv(k) for k in ["TRADIER_API_TOKEN", "TRADIER_SANDBOX_TOKEN", "TRADIER_LIVE_TOKEN"])
    checks.append(Check("tradier_token", tradier, "present" if tradier else "missing"))

    alpaca_key = any(os.getenv(k) for k in ["ALPACA_API_KEY", "ALPACA_PAPER_KEY", "ALPACA_LIVE_KEY"])
    alpaca_secret = any(os.getenv(k) for k in ["ALPACA_API_SECRET", "ALPACA_PAPER_SECRET", "ALPACA_LIVE_SECRET"])
    checks.append(Check("alpaca_creds", alpaca_key and alpaca_secret, "present" if (alpaca_key and alpaca_secret) else "missing"))

    print("Phase4 preflight")
    for c in checks:
        mark = "OK" if c.ok else "WARN"
        print(f"- [{mark}] {c.name}: {c.detail}")

    if not all(c.ok for c in checks if c.name in {"DATABASE_URL_set", "postgres_tcp_5432", "postgres_auth_query"}):
        print("Preflight: DB prerequisites not met. Ingestors may fail writes.")


if __name__ == "__main__":
    main()
