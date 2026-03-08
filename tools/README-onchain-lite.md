# onchain-lite

Lightweight local CLI for market-context research when the full `onchain` binary is unavailable.

## Commands

```bash
python3 tools/onchain-lite.py --version
python3 tools/onchain-lite.py --json test
python3 tools/onchain-lite.py --json price ethereum
python3 tools/onchain-lite.py --json markets -l 15
python3 tools/onchain-lite.py --json chains -l 12
python3 tools/onchain-lite.py --json gas --chain ethereum
python3 tools/onchain-lite.py --json polymarket sentiment ethereum -l 800
```

## Notes
- Uses public endpoints (CoinGecko, DefiLlama, Polymarket, Etherscan gas oracle).
- Built for paper-research context and quick telemetry.
