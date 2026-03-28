# Blockchain Quant Lane

This lane handles Solidity smart contracts, token/transaction tracing, and chain analytics.

## Scope
- Smart-contract research and prototyping (Hardhat)
- ERC-20 / DEX flow tracing
- Wallet clustering heuristics
- Event-driven alpha/risk signals from on-chain data

## Structure
- `hardhat/` — Solidity dev environment
- `contracts/` — audited or research contract sources
- `scripts/` — deployment/testing scripts
- `analysis/` — token flow + transaction tracing scripts

## New tracing & contract tooling

### Ethereum tx trace
```bash
python3 services/blockchain/analysis/trace_eth_tx.py 0x<txhash>
# optional: --rpc <url> --out trace_eth.json
```

### Bitcoin tx trace (UTXO flow)
```bash
python3 services/blockchain/analysis/trace_btc_tx.py <txid> --depth 1
# optional: --out trace_btc.json
```

### Solidity static risk scan
```bash
python3 services/blockchain/analysis/scan_solidity_contract.py \
  services/blockchain/hardhat/contracts/Greeter.sol
```

### Hardhat contract introspection
```bash
cd services/blockchain/hardhat
npm run introspect -- Greeter
```

## Suggested free/open-source tooling
- Hardhat + ethers.js
- Foundry (optional)
- Public JSON-RPC endpoints for exploratory tracing
- Self-hosted archival node for deep traces (`debug_traceTransaction`) in production

## Security notes
- Public RPC endpoints often disable `debug_*` methods; treat that as expected.
- Never paste private keys in scripts, logs, or traces.
- Use read-only providers for analysis tasks.
