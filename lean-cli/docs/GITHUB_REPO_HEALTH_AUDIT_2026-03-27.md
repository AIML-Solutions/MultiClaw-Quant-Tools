# GitHub Repository Health Audit (AIML-Solutions)

Generated: 2026-03-27T21:13:21.017825+00:00

## Scoring
- +2: no branch protection on default branch
- +2: latest CI run not successful
- +1: >5 open PRs
- +1: >20 open issues
- +1: >30 days since last push

## Summary Table

| Repo | Risk | Open PRs | Open Issues | Branch Protection | Last CI | Days Since Push |
|---|---:|---:|---:|---|---|---:|
| AIML-Solutions/TerraformTools | 5 | 1 | 0 | none | ci failure | 34 |
| AIML-Solutions/LangChain01 | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/LangChainTools | 3 | 0 | 0 | none | none | 55 |
| AIML-Solutions/MCP-AIML | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/OpenClawTools | 3 | 0 | 0 | none | ci success | 49 |
| AIML-Solutions/ProRepoAgentOps | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/QCLeanAlgos | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/QCLeanWorkflows | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/SnorkelTools | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/moltbot | 3 | 0 | 0 | none | none | 49 |
| AIML-Solutions/resume | 3 | 0 | 0 | none | none | 175 |
| AIML-Solutions/MultiClaw-Quant-Tools | 2 | 1 | 0 | none | Quant Quality Gate success | 19 |
| AIML-Solutions/IntelliClaw | 2 | 0 | 0 | none | none | 26 |
| AIML-Solutions/MultiClaw-Core | 2 | 0 | 0 | none | Core Quality Gate success | 19 |
| AIML-Solutions/MultiClaw-MLFlow | 2 | 0 | 0 | none | MLflow Quality Gate success | 28 |
| AIML-Solutions/MultiClaw-Public-Library | 2 | 0 | 0 | none | Library Quality Gate success | 19 |
| AIML-Solutions/aiml-solutions.com | 2 | 0 | 0 | none | Deploy to GitHub Pages success | 3 |
| AIML-Solutions/multiclaw-blockchain | 2 | 0 | 0 | none | none | 28 |
| AIML-Solutions/multiclaw-frontend | 2 | 0 | 0 | none | Deploy Next.js site to GitHub Pages success | 28 |
| AIML-Solutions/multiclaw-llm | 2 | 0 | 0 | none | none | 28 |

## Priority Hardening Actions

1. Enable branch protection on all active default branches (required PR reviews + status checks + no force push).
2. Standardize default branch names to `main` where still `master` or unset.
3. Ensure each repo has at least one green CI workflow on default branch.
4. Add CODEOWNERS + issue/PR templates + SECURITY.md for public repos.
5. Add stale PR/issue automation and dependency update automation.

## Immediate Focus Candidates

- **AIML-Solutions/TerraformTools** (risk 5): protection=none, last_ci=ci failure, PRs=1, issues=0
- **AIML-Solutions/LangChain01** (risk 3): protection=none, last_ci=none, PRs=0, issues=0
- **AIML-Solutions/LangChainTools** (risk 3): protection=none, last_ci=none, PRs=0, issues=0
- **AIML-Solutions/MCP-AIML** (risk 3): protection=none, last_ci=none, PRs=0, issues=0
- **AIML-Solutions/OpenClawTools** (risk 3): protection=none, last_ci=ci success, PRs=0, issues=0
- **AIML-Solutions/ProRepoAgentOps** (risk 3): protection=none, last_ci=none, PRs=0, issues=0
- **AIML-Solutions/QCLeanAlgos** (risk 3): protection=none, last_ci=none, PRs=0, issues=0
- **AIML-Solutions/QCLeanWorkflows** (risk 3): protection=none, last_ci=none, PRs=0, issues=0