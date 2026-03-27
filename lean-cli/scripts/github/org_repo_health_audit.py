#!/usr/bin/env python3
"""
Org-level GitHub repository health audit.

Usage:
  python3 org_repo_health_audit.py --org AIML-Solutions --out ../../docs/GITHUB_REPO_HEALTH_AUDIT.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path


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
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    repos = jrun(
        f"gh repo list {args.org} --limit {args.limit} --json "
        "nameWithOwner,name,isPrivate,defaultBranchRef,pushedAt,updatedAt,url,description"
    )
    if repos is None:
        raise SystemExit("Failed to fetch repos via gh CLI")

    now = dt.datetime.now(dt.timezone.utc)
    rows = []

    for r in repos:
        full = r["nameWithOwner"]
        default = (r.get("defaultBranchRef") or {}).get("name") or ""

        prs = jrun(f"gh pr list --repo {full} --state open --limit 100 --json number") or []
        issues = jrun(f"gh issue list --repo {full} --state open --limit 100 --json number") or []
        runs = jrun(
            f"gh run list --repo {full} --limit 1 --json "
            "conclusion,status,createdAt,updatedAt,workflowName,url"
        ) or []

        protection_state = "none"
        if default:
            rc, _, err = run(f"gh api repos/{full}/branches/{default}/protection")
            if rc == 0:
                protection_state = "enabled"
            elif "404" in err or "Branch not protected" in err:
                protection_state = "none"
            else:
                protection_state = "unknown"

        pushed = r.get("pushedAt")
        days_since_push = "n/a"
        if pushed:
            try:
                d = dt.datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                days_since_push = (now - d).days
            except Exception:
                pass

        last_run = runs[0] if runs else None
        last_ci = "none"
        ci_ok = "n/a"
        if last_run:
            last_ci = f"{last_run.get('workflowName', '?')} {last_run.get('conclusion', '?')}"
            ci_ok = (
                "yes"
                if last_run.get("conclusion") == "success" and last_run.get("status") == "completed"
                else "no"
            )

        risk = 0
        if protection_state != "enabled":
            risk += 2
        if len(prs) > 5:
            risk += 1
        if len(issues) > 20:
            risk += 1
        if last_run and ci_ok == "no":
            risk += 2
        if isinstance(days_since_push, int) and days_since_push > 30:
            risk += 1

        rows.append(
            {
                "repo": full,
                "risk": risk,
                "open_prs": len(prs),
                "open_issues": len(issues),
                "branch_protection": protection_state,
                "last_ci": last_ci,
                "days_since_push": days_since_push,
            }
        )

    rows.sort(key=lambda x: (-x["risk"], -x["open_prs"], -x["open_issues"], x["repo"]))

    out = []
    out.append(f"# GitHub Repository Health Audit ({args.org})")
    out.append("")
    out.append(f"Generated: {now.isoformat()}")
    out.append("")
    out.append("| Repo | Risk | Open PRs | Open Issues | Branch Protection | Last CI | Days Since Push |")
    out.append("|---|---:|---:|---:|---|---|---:|")
    for x in rows:
        out.append(
            f"| {x['repo']} | {x['risk']} | {x['open_prs']} | {x['open_issues']} | "
            f"{x['branch_protection']} | {x['last_ci']} | {x['days_since_push']} |"
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out))
    print(out_path)


if __name__ == "__main__":
    main()
