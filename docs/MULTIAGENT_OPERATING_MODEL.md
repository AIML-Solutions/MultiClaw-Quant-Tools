# Multi-Agent Operating Model (Quant Platform)

## Objective
Use specialized agents to speed up iteration without losing rigor or auditability.

## Agent Roles

1. **Data Agent**
   - Owns ingestion jobs, schema validation, data quality checks.
   - Produces freshness/gap reports and replay artifacts.

2. **Strategy Agent**
   - Owns sleeve code changes and signal logic.
   - Must attach matrix + walk-forward evidence for every strategy PR.

3. **Execution Agent**
   - Owns paper-trade connectors, order-state safety, slippage realism.
   - Validates fill semantics and risk controls.

4. **Research Agent**
   - Owns paper curation and hypothesis queue.
   - Delivers token-efficient digest updates and evidence mapping.

5. **Governance Agent**
   - Owns repo health, CI policies, branch protection, changelog quality.
   - Runs org audit scripts and tracks risk score deltas.

## Hand-off Contract
Every agent hand-off must include:
- objective,
- changed files,
- reproducible command list,
- artifact output paths,
- known caveats.

## Definition of Done (DoD)
A strategy change is only done if all are present:
1. Matrix run artifact
2. Walk-forward artifact
3. Data quality statement
4. Risk/cost caveats
5. PR summary with exact file paths

## Escalation Rules
- If OOS net <= 0 in >= 2 windows: sleeve marked **candidate off**.
- If data requests failure > 2%: no new alpha claims until resolved.
- If CI/governance risk score rises: freeze merges except remediation.

## Cadence
- Daily: data freshness + paper snapshot checks
- 2-3x weekly: strategy matrix reruns for active sleeves
- Weekly: walk-forward and allocator refresh
- Monthly: governance + security hardening review
