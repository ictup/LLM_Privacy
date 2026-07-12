# CV Project Bullets

Keep the `research prototype` qualifier and describe the primary endpoint as
`judge-assessed attack adoption` rather than universal attack success.

**RAGShield: Auditable Prompt-Injection Defense Evaluation for RAG Systems**
Tech stack: Python, OpenAI Responses API, SafeRAG, BM25, structured evaluation, paired statistics, hash-based audits

- Built a reproducible red-blue evaluation prototype for adversarial RAG, focused on injected retrieval content, inter-context conflict, soft advertising, semantic noise, and denial-of-service evidence.
- Implemented a layered defense pipeline with label-free context screening, conflict-preserving deduplication, untrusted-context separation, sensitive-pattern redaction, and policy-aware output validation.
- Ran a frozen real-model study with `gpt-5-mini-2025-08-07` on the peer-reviewed ACL 2025 SafeRAG benchmark; analyzed 377 of 379 untouched confirmatory cases under three paired system conditions.
- Reduced judge-assessed SafeRAG attack adoption from 71.4% to 29.7%, a 41.6 percentage-point paired reduction (95% CI: 35.8-47.7 points; exact McNemar `p < 0.0001`), while the utility-F1 difference remained inconclusive.
- Preserved reproducibility through pinned dataset/model versions, frozen development and confirmatory splits, resumable concurrent runners, completion-status checks, structured response metadata, hash-based public audits, and transparent complete-case exclusions.
- Identified silver noise as the main residual weakness: attack adoption decreased by only 7.1 points, motivating semantic provenance modeling and adaptive evaluation as follow-up research.

Short version:

**RAGShield** *(research prototype)*: Built and evaluated a layered security pipeline for RAG systems using a frozen GPT-5 mini protocol and ACL 2025 SafeRAG. Across 377 paired confirmatory cases, the full condition reduced judge-assessed attack adoption from 71.4% to 29.7% (95% CI for paired reduction: 35.8-47.7 points; `p < 0.0001`) and exposed semantic-noise robustness as the main remaining weakness.
