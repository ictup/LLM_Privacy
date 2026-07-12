# RAGShield Experiment Results

These results are from the deterministic scenario-v2 synthetic benchmark. The corpus
uses varied fictional enterprise records, but results must not be overclaimed as
real-world security guarantees or general model-security measurements.

## Setup

- Systems evaluated: 6
- Attack and mixed tests: 156
- Benign QA tests: 48
- Corpus: 240 synthetic documents across HR, medical, engineering, project, support,
  finance, tool manual, and poisoned document domains, with 32 source types.
- Dataset quality: 100% exact uniqueness; 77.5% normalized corpus uniqueness after
  removing identifiers and numbers. See `reports/data_quality.md`.

## Summary Table

| System | ASR ↓ | Leakage ↓ | Unauthorized Tools ↓ | Benign Success ↑ | Latency Overhead ↓ |
|---|---:|---:|---:|---:|---:|
| Baseline RAG | 91.7% | 63.5% | 48.7% | 95.8% | 0.000 ms |
| + Context Separation | 37.8% | 20.5% | 5.8% | 95.8% | -0.008 ms |
| + Retrieval Sanitizer | 28.2% | 21.1% | 5.8% | 100.0% | 0.634 ms |
| + PII Redaction | 16.0% | 0.0% | 5.8% | 100.0% | 0.695 ms |
| + Tool Gate | 10.3% | 0.0% | 0.0% | 100.0% | 0.681 ms |
| Full RAGShield | 0.0% | 0.0% | 0.0% | 100.0% | 0.321 ms |

## Interpretation

- The baseline retains high benign utility but fails most adversarial scenarios.
- Context separation blocks direct and indirect instruction-following attacks; retrieval
  sanitization then removes residual poisoned-evidence influence and restores benign
  failures caused by contaminated retrieval.
- Redaction, tool gating, and tenant filtering produce distinct incremental reductions,
  making the cumulative ablation easier to interpret than the original template run.
- Full RAGShield combines all layers and has no observed attack success in this fixed
  benchmark. This is an in-distribution result, not evidence of universal robustness.
- The experiment is intentionally conservative in scope: all data, secrets, tools,
  and attacks are synthetic.

## Category-Level ASR

### Baseline RAG

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 4.2% | 4.2% |
| cross_tenant_leakage | 16 | 100.0% | 87.5% | 6.2% |
| direct_prompt_injection | 24 | 95.8% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 91.7% | 91.7% | 91.7% |
| mixed_qa | 24 | 100.0% | 100.0% | 100.0% |
| retrieval_poisoning | 16 | 93.8% | 93.8% | 93.8% |
| sensitive_information_disclosure | 24 | 87.5% | 87.5% | 8.3% |
| system_prompt_leakage | 12 | 91.7% | 8.3% | 8.3% |
| tool_misuse | 16 | 68.8% | 12.5% | 68.8% |

### + Context Separation

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 16 | 100.0% | 81.2% | 0.0% |
| direct_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 24 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 16 | 93.8% | 0.0% | 0.0% |
| sensitive_information_disclosure | 24 | 79.2% | 79.2% | 0.0% |
| system_prompt_leakage | 12 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 16 | 56.2% | 0.0% | 56.2% |

### + Retrieval Sanitizer

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 16 | 100.0% | 81.2% | 0.0% |
| direct_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 24 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 16 | 0.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 24 | 79.2% | 79.2% | 0.0% |
| system_prompt_leakage | 12 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 16 | 56.2% | 6.2% | 56.2% |

### + PII Redaction

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 16 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 24 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 16 | 0.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 24 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 12 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 16 | 56.2% | 0.0% | 56.2% |

### + Tool Gate

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 16 | 100.0% | 0.0% | 0.0% |
| direct_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 24 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 16 | 0.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 24 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 12 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 16 | 0.0% | 0.0% | 0.0% |

### Full RAGShield

| Category | N | ASR | Leakage | Unauthorized Tools |
|---|---:|---:|---:|---:|
| benign_qa | 48 | 0.0% | 0.0% | 0.0% |
| cross_tenant_leakage | 16 | 0.0% | 0.0% | 0.0% |
| direct_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| indirect_prompt_injection | 24 | 0.0% | 0.0% | 0.0% |
| mixed_qa | 24 | 0.0% | 0.0% | 0.0% |
| retrieval_poisoning | 16 | 0.0% | 0.0% | 0.0% |
| sensitive_information_disclosure | 24 | 0.0% | 0.0% | 0.0% |
| system_prompt_leakage | 12 | 0.0% | 0.0% | 0.0% |
| tool_misuse | 16 | 0.0% | 0.0% | 0.0% |
