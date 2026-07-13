# SafeRAG DeepSeek Cross-Provider Rejudge Protocol

## Research Question

Does the main SafeRAG attack-adoption effect remain when the frozen GPT-5 mini
answers are judged by a different provider and model family?

## Frozen Identity

- Protocol: `saferag-deepseek-independent-rejudge-v1`
- Protocol hash: `9bed5045056899025dba08cebfb487ec8bea5a5ae8afd669824db674f184f60a`
- Source protocol: `saferag-gpt5mini-confirmatory-v6`
- Source generator: `gpt-5-mini-2025-08-07`
- Independent judge: `deepseek-v4-pro`, non-thinking mode
- Judge temperature: 0
- Judge output cap: 768 tokens
- Workers: 32
- Judge definition and option schema: the frozen SafeRAG judge v3

## Fixed Sample

The rejudge preserves the original 377-case complete-case analysis. Cases
`WDoS-41` and `WDoS-47` remain excluded across all systems, even though one could
be newly judged, so the GPT and DeepSeek estimates use the same answers and case
set. The paid run therefore contains 1,131 judgments: 377 cases by three systems.

System names, defense metadata, prompts, and model identity are not included in
the judge input. The judge receives only the question, frozen answer, numbered
options, trusted reference contexts, and attack reference contexts.

## Endpoints

- DeepSeek-assessed attack adoption for each system.
- Paired treatment-minus-baseline effects, bootstrap intervals, and exact
  McNemar tests.
- Exact agreement and Cohen's kappa between the original GPT judge and DeepSeek.
- Utility F1 and groundedness under the independent judge.

## Claim Boundary

Cross-provider rejudging reduces same-model-family correlated bias. It does not
create human ground truth, prove that either judge is correct, or remove the need
for a blinded human audit of disagreements.

Raw SafeRAG text, answers, and judgments remain local. Public artifacts contain
aggregate statistics, usage totals, and hashes of opaque response identifiers.
