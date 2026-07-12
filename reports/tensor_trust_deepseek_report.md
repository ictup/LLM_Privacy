# RAGShield Tensor Trust DeepSeek Pilot

## Study Identity

- Protocol: `tensor-trust-deepseek-pilot-v1`
- Model: `deepseek-v4-flash`
- Complete paired cases: 100 / 100
- Scoring: deterministic verbatim extraction and `Access Granted` detection

## Overall Results

| System | Raw Attack Success | Final Attack Success (95% CI) | Utility Success (95% CI) |
|---|---:|---:|---:|
| baseline | 57.0% | 57.0% (47.2%-66.3%) | 61.0% (51.2%-70.0%) |
| context_boundary | 35.0% | 35.0% (26.4%-44.7%) | 87.0% (79.0%-92.2%) |
| ragshield_full | 36.0% | 0.0% (0.0%-3.7%) | 80.0% (71.1%-86.7%) |

## Results by Task

| Task | System | Attack Success | Utility Success |
|---|---|---:|---:|
| extraction | baseline | 58.0% | 62.0% |
| extraction | context_boundary | 32.0% | 90.0% |
| extraction | ragshield_full | 0.0% | 82.0% |
| hijacking | baseline | 56.0% | 60.0% |
| hijacking | context_boundary | 38.0% | 84.0% |
| hijacking | ragshield_full | 0.0% | 78.0% |

## Paired Effects versus Baseline

| System | Attack difference (95% bootstrap CI) | Exact McNemar p | Utility difference (95% bootstrap CI) |
|---|---:|---:|---:|
| context_boundary | -22.0% (-34.0% to -10.0%) | 0.00094067 | +26.0% (+16.0% to +36.0%) |
| ragshield_full | -57.0% (-67.0% to -47.0%) | <0.00000001 | +19.0% (+9.0% to +28.0%) |

## Interpretation

- The context boundary alone reduced attack success from 57% to 35% while increasing utility from 61% to 87%.
- The full system's model output still had 36% raw attack success. Its deterministic authorization and secret-output gate reduced final attack success to 0%.
- The full gate intervened on 38.0% of attack inputs and 2.0% of utility inputs.
- This is evidence for layered system controls on the fixed sample, not evidence that prompt instructions alone eliminate attacks.

## Cost

- Input tokens: 186388
- Output tokens: 24078
- Estimated API cost at documented cache-miss rates: `$0.0328`

## Limitations

- This fixed-sample pilot is not a full benchmark run.
- Extraction scoring detects verbatim access-code leakage, not paraphrased hints.
- DeepSeek exposes a moving model alias rather than a dated snapshot in this protocol.
- The full system includes a deterministic authorization and output gate.
