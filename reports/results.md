# RAGShield Experiment Results

These results are from a deterministic offline synthetic benchmark. They are useful for
showing controlled red-blue evaluation mechanics, but they should not be overclaimed as
real-world security guarantees.

## Setup

- Systems evaluated: 6
- Attack and mixed tests: 120
- Benign QA tests: 30
- Corpus: 128 synthetic documents across HR, medical, engineering, project, support,
  finance, tool manual, and poisoned document domains.

## Summary Table

| System | ASR ↓ | Leakage ↓ | Unauthorized Tools ↓ | Benign Success ↑ | Latency Overhead ↓ |
|---|---:|---:|---:|---:|---:|
| Baseline RAG | 100.0% | 66.7% | 50.0% | 100.0% | 0.000 ms |
| + Context Separation | 16.7% | 0.0% | 0.0% | 100.0% | 0.015 ms |
| + Retrieval Sanitizer | 16.7% | 0.0% | 0.0% | 100.0% | 0.087 ms |
| + PII Redaction | 16.7% | 0.0% | 0.0% | 100.0% | 0.112 ms |
| + Tool Gate | 16.7% | 0.0% | 0.0% | 100.0% | 0.131 ms |
| Full RAGShield | 0.0% | 0.0% | 0.0% | 100.0% | 0.001 ms |

## Interpretation

- The baseline remains useful on benign QA but is intentionally vulnerable across the
  adversarial test set.
- Context separation removes direct policy leakage and most unsafe behavior in this
  synthetic setup, while remaining retrieval-poisoning failures are visible in the
  category-level summaries.
- Full RAGShield combines context separation, retrieval sanitization, fake PII/secret
  redaction, tool gating, output validation, and tenant filtering.
- The experiment is intentionally conservative in scope: all data, secrets, tools,
  and attacks are synthetic.

## Category-Level ASR

### Baseline RAG

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 100.0% | 100.0% | 0.0% |
| direct_prompt_injection | 20 | 100.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 100.0% | 100.0% | 100.0% |
| mixed_qa | 20 | 100.0% | 100.0% | 100.0% |
| retrieval_poisoning | 10 | 100.0% | 100.0% | 100.0% |
| sensitive_information_disclosure | 20 | 100.0% | 100.0% | 0.0% |
| system_prompt_leakage | 10 | 100.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 100.0% | 0.0% | 100.0% |

### + Context Separation

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 20 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 10 | 100.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 20 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 10 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 0.0% | 0.0% | 0.0% |

### + Retrieval Sanitizer

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 20 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 10 | 100.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 20 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 10 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 0.0% | 0.0% | 0.0% |

### + PII Redaction

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 20 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 10 | 100.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 20 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 10 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 0.0% | 0.0% | 0.0% |

### + Tool Gate

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 20 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 10 | 100.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 20 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 10 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 0.0% | 0.0% | 0.0% |

### Full RAGShield

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 30 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 10 | 0.0% | 0.0% | 0.0% |
| direct_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 20 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 20 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 10 | 0.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 20 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 10 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 10 | 0.0% | 0.0% | 0.0% |
