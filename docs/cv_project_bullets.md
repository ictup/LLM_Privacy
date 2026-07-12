# CV Project Bullets

Use this version after referencing the repository and synthetic benchmark results.

**RAGShield: Automated Red-Blue Teaming for Privacy Leakage and Prompt-Injection Defense in RAG Agents**  
Tech stack: Python, deterministic RAG evaluation, synthetic security benchmark, policy-based tool gating, JSONL tracing, unit tests

- Built a defensive red-blue evaluation prototype for RAG-enabled and tool-using LLM agents, covering direct and indirect prompt injection, sensitive information disclosure, system prompt leakage, tool misuse, retrieval poisoning, and cross-tenant leakage.
- Designed a synthetic benchmark with 128 labeled documents, 100 adversarial tests, 20 mixed tests, and 30 benign QA tests using only fake PII, fake secrets, toy tools, and controlled tenant metadata.
- Implemented defense modules for untrusted-context separation, retrieval sanitization, fake PII/secret redaction, policy-aware output validation, least-privilege tool-call gating, tenant filtering, and audit-friendly JSONL traces.
- Evaluated baseline and defense ablations under attack success rate, leakage rate, unauthorized tool-call rate, poisoned retrieval influence, benign task success, and latency overhead.
- In the deterministic synthetic benchmark, reduced attack success rate from 100.0% for the baseline to 0.0% for the full defense configuration while preserving 100.0% benign QA success; documented limitations and residual research questions separately.

Short version:

**RAGShield** *(research prototype)*: Built a synthetic red-blue evaluation platform for privacy leakage and prompt-injection defense in RAG agents, implementing retrieval sanitization, PII/secret redaction, output validation, least-privilege tool gating, tenant filtering, audit traces, and ablation metrics.
