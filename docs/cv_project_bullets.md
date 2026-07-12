# CV Project Bullets

Use this version after referencing the repository and synthetic benchmark results.

**RAGShield: Automated Red-Blue Teaming for Privacy Leakage and Prompt-Injection Defense in RAG Agents**  
Tech stack: Python, deterministic RAG evaluation, synthetic security benchmark, policy-based tool gating, JSONL tracing, unit tests

- Built a defensive red-blue evaluation prototype for RAG-enabled and tool-using LLM agents, covering direct and indirect prompt injection, sensitive information disclosure, system prompt leakage, tool misuse, retrieval poisoning, and cross-tenant leakage.
- Designed a synthetic benchmark with 240 varied enterprise documents across 32 source types, 132 adversarial tests, 24 mixed tests, and 48 benign QA tests using only fake PII, fake secrets, toy tools, and controlled tenant metadata.
- Added automated dataset-quality checks for exact and normalized duplication, metadata completeness, split coverage, and 152 target-document references; achieved 100% exact uniqueness and 77.5% normalized corpus uniqueness after removing IDs and numbers.
- Implemented defense modules for untrusted-context separation, retrieval sanitization, fake PII/secret redaction, policy-aware output validation, least-privilege tool-call gating, tenant filtering, and audit-friendly JSONL traces.
- Evaluated baseline and defense ablations under attack success rate, leakage rate, unauthorized tool-call rate, poisoned retrieval influence, benign task success, and latency overhead.
- In the deterministic scenario-v2 benchmark, reduced attack success rate from 91.7% for the baseline to 0.0% for the full configuration while improving target-citation-based benign QA success from 95.8% to 100.0%; documented limitations and residual research questions separately.

Short version:

**RAGShield** *(research prototype)*: Built a synthetic red-blue evaluation platform for privacy leakage and prompt-injection defense in RAG agents, implementing retrieval sanitization, PII/secret redaction, output validation, least-privilege tool gating, tenant filtering, audit traces, and ablation metrics.
