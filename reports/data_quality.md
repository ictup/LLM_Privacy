# Dataset Quality Report

The benchmark contains synthetic organizational scenarios only. Diversity metrics are
reported to make template repetition and dataset limitations visible.

## Diversity

| Split | Rows | Exact unique | Normalized unique | Avg. words | Vocabulary |
|---|---:|---:|---:|---:|---:|
| Corpus | 240 | 100.0% | 77.5% | 37.8 | 401 |
| Attacks | 132 | 100.0% | 100.0% | 17.3 | 396 |
| Benign | 48 | 100.0% | 100.0% | 15.8 | 94 |
| Mixed | 24 | 100.0% | 100.0% | 22.7 | 83 |

Normalized uniqueness removes document identifiers and numbers before comparison,
so it is stricter than ordinary duplicate detection.

## Coverage

| Validation | Result |
|---|---:|
| Source types | 32 |
| Complete document metadata | 100.0% |
| Referenced targets | 152 |
| Missing targets | 0 |
| Validation passed | True |

### Domain Distribution

| Domain | Documents |
|---|---:|
| engineering | 30 |
| finance | 30 |
| hr | 30 |
| medical | 30 |
| poisoned | 30 |
| project | 30 |
| support | 30 |
| tool_manual | 30 |

### Attack Distribution

| Category | Tests |
|---|---:|
| cross_tenant_leakage | 16 |
| direct_prompt_injection | 24 |
| indirect_prompt_injection | 24 |
| retrieval_poisoning | 16 |
| sensitive_information_disclosure | 24 |
| system_prompt_leakage | 12 |
| tool_misuse | 16 |

## Remaining Limitations

- Scenario combinations are deterministic and authored from controlled templates.
- Fictional English enterprise text does not reproduce every real document style or language.
- A lexical retriever and deterministic answerer make this a systems benchmark, not a model leaderboard.