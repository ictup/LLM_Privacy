# CV Project Bullets

Use this version after referencing the repository and benchmark reports.

**RAGShield: Automated Red-Blue Teaming for Privacy Leakage and Prompt-Injection Defense in RAG Agents**  
Tech stack: Python, SafeRAG, deterministic RAG evaluation, benchmark adapters, policy-based tool gating, JSONL tracing, unit tests

- Built a defensive red-blue evaluation prototype for RAG-enabled and tool-using LLM agents, covering direct and indirect prompt injection, sensitive information disclosure, system prompt leakage, tool misuse, retrieval poisoning, and cross-tenant leakage.
- Designed a synthetic benchmark with 240 varied enterprise documents across 32 source types, 132 adversarial tests, 24 mixed tests, and 48 benign QA tests using only fake PII, fake secrets, toy tools, and controlled tenant metadata.
- Added automated dataset-quality checks for exact and normalized duplication, metadata completeness, split coverage, and 152 target-document references; achieved 100% exact uniqueness and 77.5% normalized corpus uniqueness after removing IDs and numbers.
- Implemented defense modules for untrusted-context separation, retrieval sanitization, fake PII/secret redaction, policy-aware output validation, least-privilege tool-call gating, tenant filtering, and audit-friendly JSONL traces.
- Evaluated baseline and defense ablations under attack success rate, leakage rate, unauthorized tool-call rate, poisoned retrieval influence, benign task success, and latency overhead.
- Integrated the ACL 2025 SafeRAG benchmark through a pinned, hash-verified adapter covering 387 Chinese security cases; because the upstream repository lacks explicit redistribution terms, added a direct-source fetch workflow rather than republishing the raw files.
- In an offline SafeRAG architecture test, measured 52.9% retrieval accuracy and 89.1% attack-context exposure for lexical RAG versus 96.5% and 0.0% under an oracle-like trusted-source retrieval condition; clearly separated this provenance upper bound from LLM-based benchmark claims.
- In the deterministic scenario-v2 benchmark, reduced attack success rate from 91.7% for the baseline to 0.0% for the full configuration while improving target-citation-based benign QA success from 95.8% to 100.0%; documented limitations and residual research questions separately.

Short version:

**RAGShield** *(research prototype)*: Built a red-blue evaluation platform for privacy leakage and prompt-injection defense in RAG agents, combining controlled synthetic ablations with a pinned SafeRAG adapter, retrieval sanitization, PII/secret redaction, least-privilege tool gating, tenant filtering, and audit traces.
