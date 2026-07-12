# CV Project Bullets

Use the measured version below. Keep the `research prototype` qualifier and do not replace
`judge-assessed attack adoption` with a broader claim such as universal attack success.

**RAGShield: Automated Red-Blue Teaming for Privacy Leakage and Prompt-Injection Defense in RAG Agents**  
Tech stack: Python, OpenAI Responses API, SafeRAG, BM25, structured evaluation, policy-based tool gating, JSONL tracing, unit tests

- Built a reproducible red-blue evaluation prototype for RAG-enabled and tool-using LLM agents, covering prompt injection, sensitive-data disclosure, tool misuse, retrieval poisoning, and cross-tenant leakage.
- Implemented a layered defense pipeline with label-free context screening, conflict-preserving deduplication, untrusted-context separation, fake PII/secret redaction, output validation, tenant filtering, and least-privilege tool authorization.
- Ran a frozen real-model study with `gpt-5-mini-2025-08-07` on the peer-reviewed ACL 2025 SafeRAG benchmark; analyzed 377 of 379 untouched confirmatory cases under three paired system conditions.
- Reduced judge-assessed SafeRAG attack adoption from 71.4% to 29.7% with the full stack, a 41.6 percentage-point paired reduction (95% CI: 35.8-47.7 points; exact McNemar `p < 0.0001`) while utility-F1 change remained inconclusive.
- Added 612 real-model controlled canary responses over author-generated privacy, tenant, retrieval, and toy-tool tests; measured 0% leakage, unauthorized tool calls, and aggregate attack success for the full stack in this controlled run, while explicitly limiting the claim to component evidence.
- Preserved reproducibility through pinned dataset/model versions, frozen development and confirmatory splits, resumable concurrent runners, structured response metadata, hash-based public audits, and transparent complete-case exclusions.
- Identified SN as a residual weakness: attack adoption decreased by only 7.1 points, motivating semantic provenance modeling and adaptive evaluation as follow-up research.

Short version:

**RAGShield** *(research prototype)*: Built and evaluated a layered security pipeline for RAG agents using a frozen GPT-5 mini protocol and ACL 2025 SafeRAG. Across 377 paired confirmatory cases, the full stack reduced judge-assessed attack adoption from 71.4% to 29.7% (95% CI for paired reduction: 35.8-47.7 points; `p < 0.0001`) and exposed semantic-noise robustness as the main remaining weakness.
