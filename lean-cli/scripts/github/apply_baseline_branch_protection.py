#!/usr/bin/env python3
"""
Apply non-blocking baseline branch protection for org repositories.

This baseline does NOT add review/check requirements (to avoid accidental lockouts),
but prevents force-push and branch deletion on default branches.

Usage:
  python3 apply_baseline_branch_protection.py --org AIML-Solutions --limit 100
"""

from __future__ import annotations

import argparse
import json
import subprocess


def run(cmd: str):
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def jrun(cmd: str):
    rc, out, _ = run(cmd)
    if rc != 0 or not out:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repos = jrun(
        f"gh repo list {args.org} --limit {args.limit} --json nameWithOwner,defaultBranchRef"
    )
    if repos is None:
        raise SystemExit("Failed to fetch repos")

    payload = {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "required_conversation_resolution": False,
        "lock_branch": False,
        "allow_fork_syncing": True,
    }

    print(f"Applying baseline protection for org={args.org} (dry_run={args.dry_run})")

    for r in repos:
        full = r["nameWithOwner"]
        default = (r.get("defaultBranchRef") or {}).get("name")

        if not default:
            print(f"[skip] {full} (no default branch)")
            continue

        cmd = (
            f"gh api -X PUT repos/{full}/branches/{default}/protection "
            f"-H 'Accept: application/vnd.github+json' --input - <<'JSON'\n"
            f"{json.dumps(payload, indent=2)}\nJSON"
        )

        if args.dry_run:
            print(f"[dry-run] {full} ({default})")
            continue

        rc, _, err = run(cmd)
        if rc == 0:
            print(f"[ok] {full} ({default})")
        else:
            print(f"[error] {full} ({default}) -> {err[:200]}")


if __name__ == "__main__":
    main()
