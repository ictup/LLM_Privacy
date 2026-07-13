# SafeRAG Cross-Provider DeepSeek Rejudge

## Study Identity

- Protocol: `saferag-deepseek-independent-rejudge-v1`
- Source generator: `gpt-5-mini-2025-08-07`
- Original judge: `gpt-5-mini-2025-08-07`
- Independent judge: `deepseek-v4-pro`
- Confirmatory cases: 377
- Independent judgments: 1131
- System identity was not included in the judge input.

## DeepSeek Rejudge Results

| System | N | Attack adoption (95% CI) | Utility F1 | Grounded |
|---|---:|---:|---:|---:|
| baseline | 377 | 60.2% (55.2%-65.0%) | 19.4% | 57.0% |
| context_boundary | 377 | 34.7% (30.1%-39.7%) | 21.8% | 83.0% |
| ragshield_full | 377 | 22.0% (18.1%-26.5%) | 17.0% | 70.6% |

## Paired Effects

| Treatment | Attack difference (95% CI) | McNemar p | Utility difference (95% CI) |
|---|---:|---:|---:|
| context_boundary | -0.255 [-0.313, -0.196] | <0.0001 | 0.025 [-0.008, 0.057] |
| ragshield_full | -0.382 [-0.440, -0.324] | <0.0001 | -0.023 [-0.054, 0.007] |

## Agreement With Original GPT Judge

| Scope | N | Exact agreement | Cohen kappa |
|---|---:|---:|---:|
| Overall | 1131 | 74.3% | 0.479 |
| baseline | 377 | 75.6% | 0.465 |
| context_boundary | 377 | 70.8% | 0.381 |
| ragshield_full | 377 | 76.4% | 0.389 |

## Execution Evidence

- Unique DeepSeek response IDs: 1131
- Input tokens: 1678626
- Output tokens: 202354
- Estimated cache-miss cost: `$0.9062`

## Limitations

- DeepSeek provides cross-provider automatic judgment, not human ground truth.
- The rejudge preserves the original 377-case complete-case sample and frozen GPT answers.
- Judge agreement does not establish correctness when both automatic judges share a bias.