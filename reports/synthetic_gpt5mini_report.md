# RAGShield GPT-5 mini Controlled Canary Study

- Protocol: `ragshield-controlled-canary-gpt5mini-v1`
- Model: `gpt-5-mini-2025-08-07`
- Real API responses: 612
- Input/output tokens: 434156 / 263984
- Estimated API cost at documented standard rates: $0.64

| System | N | ASR | Leakage | Unauthorized Tools | Benign Success | Latency ms |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 204 | 30.8% | 11.5% | 10.3% | 97.9% | 5763.6 |
| context_boundary | 204 | 26.3% | 9.0% | 0.6% | 100.0% | 5458.7 |
| ragshield_full | 204 | 0.0% | 0.0% | 0.0% | 97.9% | 5934.6 |

## Limitations

- The canary corpus is author-generated and does not establish external validity.
- Security markers are synthetic and intentionally machine-detectable.
- Use SafeRAG, not this canary study, for the primary research claim.