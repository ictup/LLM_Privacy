# SafeRAG Real-LLM Pilot

This report contains actual OpenAI Responses API generations. Both systems receive
the same mixed clean and attack contexts; only the developer instruction differs.

- Requested model: `gpt-5.6-luna`
- SafeRAG commit: `e8f579743b23e0a3937076dcc0792fe29027cba3`
- Protocol: `saferag-controlled-generation-v1`
- API key storage: process environment only; never written to this report
- Metric: exact propagation of SafeRAG attack keywords in model output
- Contexts: up to 3 labeled attack contexts, then clean contexts up to 6 total

## Execution Evidence

- Response rows: 16
- Unique response IDs: 16
- Response models: gpt-5.6-luna
- Total tokens: 10991
- Paired context hash mismatches: 0

## Overall

| System | N | Attack Keyword Cases | Avg. Keyword Ratio | Input Tokens | Output Tokens |
|---|---:|---:|---:|---:|---:|
| baseline | 8 | 33.3% | 33.3% | 3122 | 1959 |
| ragshield_context_boundary | 8 | 50.0% | 33.3% | 3514 | 2396 |

## By Task

| System | Task | N | Attack Keyword Cases | Avg. Keyword Ratio |
|---|---|---:|---:|---:|
| baseline | ICC | 2 | 0.0% | 0.0% |
| baseline | SA | 2 | 100.0% | 100.0% |
| baseline | SN | 2 | n/a | n/a |
| baseline | WDoS | 2 | 0.0% | 0.0% |
| ragshield_context_boundary | ICC | 2 | 100.0% | 50.0% |
| ragshield_context_boundary | SA | 2 | 50.0% | 50.0% |
| ragshield_context_boundary | SN | 2 | n/a | n/a |
| ragshield_context_boundary | WDoS | 2 | 0.0% | 0.0% |

## Interpretation

In this pilot, the labeled-case keyword rate is 33.3% for the baseline and 50.0% for the defended prompt.
This is not evidence that the defense improves security.

Exact keyword matching counts a term even when the model cites it only to flag a
conflict. Adoption-versus-mention must be judged separately before drawing efficacy
conclusions.

## Limitations

- Attack-keyword propagation is objective but does not measure full answer utility.
- The baseline and defended prompts receive the same mixed clean/attack contexts.
- Contexts are built from SafeRAG's labeled records, not reproduced BM25 retrieval.
- SN has no attack-keyword labels and requires a separate answer-quality judge.
- A separate blinded or human judge is still required for publishable answer-quality claims.