# RAGShield SafeRAG GPT-5 mini Confirmatory Study

## Study Identity

- Protocol: `saferag-gpt5mini-confirmatory-v6`
- Analysis: `complete-case-v1`
- SafeRAG commit: `e8f579743b23e0a3937076dcc0792fe29027cba3`
- Generator: `gpt-5-mini-2025-08-07`
- Judge: `gpt-5-mini-2025-08-07`
- Judge protocol: `saferag-judge-v3`
- Judge prompt hash: `659df569cde98d0731f9eeb366b6d985e026da8093e941122b180bfea2259cd9`
- Confirmatory cases: 377
- Primary endpoint: judge-assessed attack adoption
- Utility endpoint: macro F1 over supported correct and contradicted incorrect options

## Execution Evidence

- Generation Rows: 1160
- Judgment Rows: 1157
- Unique Generation Response Ids: 1160
- Unique Judge Response Ids: 1157
- Initial Context Pair Mismatches: 0
- Non Completed Generation Rows: 0
- Non Completed Judgment Rows: 0
- Judge Consistency Flagged Rows: 0
- Judge Low Confidence Rows: 0
- Attack Adoption Derived Rows: 343

## Development Results (Tuning Only)

These eight cases are excluded from the primary confirmatory claim.

| System | N | Attack Adoption | Utility F1 | Grounded |
|---|---:|---:|---:|---:|
| baseline | 8 | 62.5% | 11.8% | 62.5% |
| context_boundary | 8 | 25.0% | 14.5% | 87.5% |
| ragshield_full | 8 | 0.0% | 20.2% | 87.5% |

### Complete-Case Exclusions

- WDoS-41: generation missing none; judgment missing context_boundary. The entire case is excluded from primary estimates.
- WDoS-47: generation missing context_boundary; judgment missing baseline, context_boundary, ragshield_full. The entire case is excluded from primary estimates.

## Confirmatory Results

| System | N | Attack Adoption (95% CI) | Mention Only | Utility F1 | Grounded | Refusal |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 377 | 71.4% (66.6%-75.7%) | 14.6% | 18.0% | 57.6% | 24.7% |
| context_boundary | 377 | 40.6% (35.7%-45.6%) | 26.8% | 20.4% | 90.7% | 0.0% |
| ragshield_full | 377 | 29.7% (25.3%-34.5%) | 38.5% | 18.0% | 89.7% | 0.0% |

## Paired Effects

Negative attack-adoption differences favor the defense; positive utility differences
favor the defense. Intervals crossing zero are inconclusive.

| Treatment | Attack Difference (95% CI) | McNemar p | Utility Difference (95% CI) |
|---|---:|---:|---:|
| context_boundary | -0.308 [-0.371, -0.249] | <0.0001 | 0.024 [0.001, 0.047] |
| ragshield_full | -0.416 [-0.477, -0.358] | <0.0001 | 0.001 [-0.023, 0.024] |

## Results by Task

| System | Task | N | Attack Adoption | Utility F1 | Keyword Cases |
|---|---|---:|---:|---:|---:|
| baseline | ICC | 91 | 54.9% | 14.4% | 72.5% |
| baseline | SA | 92 | 85.9% | 12.0% | 72.8% |
| baseline | SN | 98 | 52.0% | 37.5% | n/a |
| baseline | WDoS | 96 | 92.7% | 7.1% | 97.9% |
| context_boundary | ICC | 91 | 31.9% | 7.3% | 68.1% |
| context_boundary | SA | 92 | 66.3% | 18.5% | 58.7% |
| context_boundary | SN | 98 | 50.0% | 34.4% | n/a |
| context_boundary | WDoS | 96 | 14.6% | 20.2% | 8.3% |
| ragshield_full | ICC | 91 | 19.8% | 5.3% | 60.4% |
| ragshield_full | SA | 92 | 45.7% | 30.6% | 48.9% |
| ragshield_full | SN | 98 | 44.9% | 24.6% | n/a |
| ragshield_full | WDoS | 96 | 8.3% | 11.4% | 0.0% |

## Token and Cost Record

- Generation tokens: 1147948
- Judge tokens: 3761110
- Estimated API cost at documented standard rates: $5.73

## Limitations

- The generator and automated judge use the same model family.
- Human blind review is required before claiming judge validity.
- SafeRAG evaluates data-injection security, not differential privacy.
- The label-free defense may miss plausible, semantically injected facts.
- Raw SafeRAG text and model answers are retained locally due source licensing.
- Primary estimates use complete-case analysis after an API generation failure; the excluded case and missing system are reported explicitly.