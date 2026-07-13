# SafeRAG Silver Noise Semantic-Defense Study

## Study Identity

- Protocol: `saferag-silver-noise-deepseek-semantic-v1`
- SafeRAG commit: `e8f579743b23e0a3937076dcc0792fe29027cba3`
- Semantic verifier and generator: `deepseek-v4-flash`
- Judge: `deepseek-v4-pro`
- Confirmatory cases: 98
- The semantic verifier received no attack labels, correct options, or golden contexts.

## Confirmatory Results

| System | N | Attack adoption (95% CI) | Utility F1 | Grounded | Refusal | Contexts |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 98 | 38.8% (29.7%-48.7%) | 37.6% | 95.9% | 0.0% | 6.00 |
| context_boundary | 98 | 46.9% (37.4%-56.7%) | 31.7% | 94.9% | 1.0% | 6.00 |
| ragshield_full | 98 | 40.8% (31.6%-50.7%) | 26.6% | 96.9% | 2.0% | 5.89 |
| semantic_provenance | 98 | 33.7% (25.1%-43.5%) | 21.6% | 86.7% | 10.2% | 5.49 |

## Primary Comparison

Semantic provenance minus current full defense:

- Attack-adoption difference: -0.071 (95% CI -0.173 to 0.031; McNemar 0.2478)
- Utility-F1 difference: -0.050 (95% CI -0.096 to -0.003)

## Label-Blind Screening Quality

- Attack-context quarantine recall: 6.1%
- Clean-context retention rate: 89.1%
- Quarantine precision: 36.0%
- Mean quarantined contexts per case: 0.51

## Execution Evidence

- semantic_screening: 100 rows, 94707 tokens, `$0.0165` estimated
- generation: 400 rows, 268160 tokens, `$0.0459` estimated
- judging: 400 rows, 815160 tokens, `$0.3877` estimated
- Estimated total cache-miss cost: `$0.4501`

## Limitations

- The semantic verifier has no external source metadata and may rely on model priors.
- Generator and judge are different DeepSeek models from the same provider.
- The study uses one deterministic generation per system and case.
- This task-specific experiment does not establish generalization beyond Chinese SafeRAG Silver Noise.