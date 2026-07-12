# RAGShield: Final GPT-5 Mini Interview Evidence

## Main Finding

On 377 complete paired SafeRAG confirmatory cases, the full RAGShield stack reduced judge-assessed attack adoption from 71.4% to 29.7%, a 58.4% relative reduction.

## External Benchmark Evidence

| System | N | Attack adoption | Grounded | Utility F1 |
|---|---:|---:|---:|---:|
| baseline | 377 | 71.4% | 57.6% | 18.0% |
| context_boundary | 377 | 40.6% | 90.7% | 20.4% |
| ragshield_full | 377 | 29.7% | 89.7% | 18.0% |

Full defense minus baseline: -41.6 percentage points (95% CI -47.7 to -35.8); McNemar p <0.0001.
Utility F1 difference: 0.001 (95% CI -0.023 to 0.024); inconclusive because the interval crosses zero.

| Task | N | Baseline adoption | Full adoption | Difference |
|---|---:|---:|---:|---:|
| ICC | 91 | 54.9% | 19.8% | -35.2 pp |
| SA | 92 | 85.9% | 45.7% | -40.2 pp |
| SN | 98 | 52.0% | 44.9% | -7.1 pp |
| WDoS | 96 | 92.7% | 8.3% | -84.4 pp |

## Controlled Privacy and Tool Evidence

| System | N | ASR | Leakage | Unauthorized tools | Benign success |
|---|---:|---:|---:|---:|---:|
| baseline | 204 | 30.8% | 11.5% | 10.3% | 97.9% |
| context_boundary | 204 | 26.3% | 9.0% | 0.6% | 100.0% |
| ragshield_full | 204 | 0.0% | 0.0% | 0.0% | 97.9% |

## Execution and Cost

- Model snapshot: `gpt-5-mini-2025-08-07`
- SafeRAG protocol: `saferag-gpt5mini-confirmatory-v6` / `complete-case-v1`
- SafeRAG generation/judgment rows: 1160 / 1157
- Automated-judge consistency flags: 0
- Controlled canary API responses: 612
- Final evidence-run estimated API cost: $6.37

## Claim Boundary

Supported:
- Under the frozen protocol, RAGShield reduced judge-assessed SafeRAG attack adoption.
- The complete stack blocked all measured synthetic canary violations in this run.
- The largest SafeRAG gains were on WDoS and ICC; SN remained the hardest task.

Not supported:
- Production-grade security against arbitrary adaptive attacks.
- Differential privacy, federated learning, or homomorphic encryption.
- Independent judge validity before blinded human review is completed.

## Required Follow-Up

Complete the generated 48-answer blinded human review before treating the automated judge as independently validated.