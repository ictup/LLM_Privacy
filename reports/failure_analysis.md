# RAGShield Failure Analysis

This report records the main residual risks and negative results. It is based on
the committed aggregate result files and does not expose raw benchmark prompts,
model answers, secrets, or private records.

## SafeRAG: Semantically Plausible Noise Remains Difficult

Full RAGShield reduced overall judge-assessed attack adoption from 71.4% to
29.7%, but the effect varied substantially by attack family.

| Task | Baseline adoption | Full adoption | Reduction |
|---|---:|---:|---:|
| Inter-context conflict | 54.9% | 19.8% | 35.2 pp |
| Soft advertising | 85.9% | 45.7% | 40.2 pp |
| Silver noise | 52.0% | 44.9% | **7.1 pp** |
| White denial of service | 92.7% | 8.3% | 84.4 pp |

The rule-based screener recognizes explicit instructions, promotional signals,
and answer-suppression patterns. Silver Noise looks like ordinary relevant
evidence, so lexical attack signatures provide little separation. This is the
clearest motivation for learned provenance and semantic contradiction models.

Full-system option F1 was 18.0%, effectively unchanged from the 18.0% baseline;
the paired confidence interval crossed zero. The experiment therefore does not
establish utility preservation or improvement.

## TAB: Coverage and Over-Redaction Trade Off

The NER/combined detector reached 61.0% character F1 and 67.4% full-coverage
recall, but retained only 78.3% of document text and falsely redacted 10.7% of
all characters.

Weakest full-coverage categories were `MISC` (14.1%), `PERSON` (37.5%),
`QUANTITY` (39.4%), and `DEM` (45.6%). A generic entity recognizer is therefore
not a complete anonymization policy. Domain adaptation and risk-weighted entity
handling are required before deployment.

## Tensor Trust: The Model Layer Is Still Vulnerable

The context boundary reduced attack success from 57% to 35%. The full system's
raw model output remained vulnerable at 36%; the deterministic authorization and
secret-output gate produced the final 0%. The gate intervened on 38% of attack
inputs and 2% of valid-access inputs.

This is a positive result for layered enforcement, but a negative result for
prompt-only defenses. The final zero must never be presented as the model itself
becoming injection-proof. Valid-access success was 80% for the full system,
below the context boundary's 87%.

## PrivacyLens: Lowest Leakage Costs Helpfulness

| System | Leakage | Helpful | Block rate |
|---|---:|---:|---:|
| Baseline | 56% | 94% | 0% |
| Privacy prompt | 14% | 94% | 0% |
| Output validator | 14% | 58% | 42% |
| Full RAGShield | 6% | 80% | 14% |

The output validator alone over-blocked and lost 36 percentage points of
helpfulness. Full RAGShield achieved the lowest leakage, but lost 14 helpfulness
points relative to baseline. Under this pilot, the privacy prompt is the best
measured security-utility trade-off, while the full system is the most
conservative choice.

The two automatic judges agreed on 96% of full-system leakage decisions, but
Cohen's kappa was 0.485 because leakage was rare and chance agreement was high.
Both judges come from the same provider, and no human annotations validate their
decisions.

## Controlled Security Path: Functional, Not Population Evidence

The integrated regression passed all nine tenant, context, output, tool, and
audit checks. These checks use small controlled fixtures and side-effect-free
tools. They prove composition and fail-closed behavior in tested cases, not
real-world rates for cross-tenant leakage or unauthorized tool use.

## Research Priorities

1. Learn source provenance and semantic conflict rather than adding keyword rules.
2. Calibrate privacy validators to reduce unnecessary blocking.
3. Add independent-provider and human validation for automatic judge endpoints.
4. Repeat stochastic runs and evaluate additional generator and retriever families.
5. Test adaptive attacks against the complete retrieval-to-tool execution path.
