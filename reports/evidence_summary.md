# RAGShield Unified Evidence and Ablation Summary

## Evidence Scorecard

| Benchmark | Evidence | N | Security: baseline -> selected | Utility: baseline -> selected | Selected system |
|---|---|---:|---:|---:|---|
| SafeRAG | `external_peer_reviewed_real_model` | 377 | 71.4% -> 29.7% | 18.0% -> 18.0% | `ragshield_full` |
| TAB | `external_peer_reviewed_human_annotated_offline` | 127 | 0.0% -> 61.0% | 100.0% -> 78.3% | `combined` |
| Tensor Trust | `external_peer_reviewed_real_model` | 100 | 57.0% -> 0.0% | 61.0% -> 80.0% | `ragshield_full` |
| PrivacyLens | `external_peer_reviewed_real_model_dual_auto_judge` | 50 | 56.0% -> 6.0% | 94.0% -> 80.0% | `ragshield_full` |

## Interpretation

- **SafeRAG:** Strong overall reduction; Silver Noise remains weak.
- **TAB:** NER adds coverage but over-redacts document text.
- **Tensor Trust:** Final zero relies on deterministic authorization and output gating.
- **PrivacyLens:** Lowest leakage has a 14-point helpfulness cost; prompt-only is the best measured trade-off.

## Complete Ablations

### Saferag

| System | N | Attack adoption (lower) | Option F1 (higher) |
|---|---:|---:|---:|
| `baseline` | 377 | 71.4% | 18.0% |
| `context_boundary` | 377 | 40.6% | 20.4% |
| `ragshield_full` | 377 | 29.7% | 18.0% |

### Tab

| System | N | Character F1 (higher) | Text retention (higher) |
|---|---:|---:|---:|
| `regex_rules` | 127 | 0.0% | 100.0% |
| `spacy_ner` | 127 | 61.0% | 78.3% |
| `combined` | 127 | 61.0% | 78.3% |

### Tensor Trust

| System | N | Attack success (lower) | Valid access (higher) |
|---|---:|---:|---:|
| `baseline` | 100 | 57.0% | 61.0% |
| `context_boundary` | 100 | 35.0% | 87.0% |
| `ragshield_full` | 100 | 0.0% | 80.0% |

### Privacylens

| System | N | Leakage (lower) | Helpful (higher) |
|---|---:|---:|---:|
| `baseline` | 50 | 56.0% | 94.0% |
| `privacy_prompt` | 50 | 14.0% | 94.0% |
| `output_validator` | 50 | 14.0% | 58.0% |
| `ragshield_full` | 50 | 6.0% | 80.0% |

### Saferag Deepseek Rejudge

| System | N | Attack adoption (lower) | Option F1 (higher) |
|---|---:|---:|---:|
| `baseline` | 377 | 60.2% | 19.4% |
| `context_boundary` | 377 | 34.7% | 21.8% |
| `ragshield_full` | 377 | 22.0% | 17.0% |

### Silver Noise Semantic

| System | N | Attack adoption (lower) | Option F1 (higher) |
|---|---:|---:|---:|
| `baseline` | 98 | 38.8% | 37.6% |
| `context_boundary` | 98 | 46.9% | 31.7% |
| `ragshield_full` | 98 | 40.8% | 26.6% |
| `semantic_provenance` | 98 | 33.7% | 21.6% |

## Integrity Checks

- [x] `saferag_complete_paired_cases`
- [x] `tab_full_official_test_split`
- [x] `tensor_trust_complete_paired_cases`
- [x] `privacylens_complete_paired_cases`
- [x] `saferag_cross_provider_rejudge_complete`
- [x] `silver_noise_semantic_study_complete`
- [x] `integrated_control_regression`

## Evidence Totals

- External peer-reviewed benchmarks: 4
- Evaluated external units across benchmark primary analyses: 654
- DeepSeek response IDs across completed studies: 3231
- Integrated deterministic checks: 9

Counts are not pooled into one effectiveness estimate because the benchmarks measure different tasks.

## Claim Boundary

Supported:

- Measured effects under each frozen benchmark protocol.
- Paired module comparisons within SafeRAG, Tensor Trust, and PrivacyLens.
- Cross-provider rejudging reproduces the direction of the main SafeRAG effect.
- The Silver Noise semantic-defense study exposes a non-significant security signal and significant utility cost.
- TAB span-detection performance against official human annotations.
- Composition and fail-closed behavior of the integrated controls on fixtures.

Not supported:

- Production-grade or universal LLM security.
- Generalization to untested model families, languages, or adaptive attacks.
- Human-validated accuracy for the automatic LLM judges.
- Differential privacy, federated learning, or homomorphic encryption.
