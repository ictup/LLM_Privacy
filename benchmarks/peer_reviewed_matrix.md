# Peer-Reviewed Benchmark Matrix

This matrix separates datasets that have been downloaded and validated from papers that
are only relevant future work. Raw benchmark data stays under `data/external/` and is not
redistributed by this repository.

| Benchmark | Peer-reviewed source | Primary RAGShield claim | Local status |
|---|---|---|---|
| SafeRAG | ACL 2025 Long Paper | Indirect prompt injection and retrieval manipulation | 377-case GPT-5 mini study complete |
| TAB | Computational Linguistics 2022 | PII detection and text anonymization | Full 127-document official test split evaluated offline |
| Tensor Trust v1 | ICLR 2024 | Direct prompt hijacking and prompt/secret extraction | 100-case, 600-call paired DeepSeek study complete |
| PrivacyLens | NeurIPS 2024 Datasets and Benchmarks | Contextual privacy leakage in agent actions | 50-case, 600-call paired DeepSeek study complete |

## What "Real" Means Here

- Tensor Trust contains attacks written by human players.
- TAB contains real public court text with manual privacy annotations.
- PrivacyLens scenarios are grounded in regulations, privacy literature, and
  crowdsourcing, while personas and sensitive values remain safe research fixtures.
- PrivacyLens contains realistic but constructed agent trajectories; it is not private victim data.

No benchmark should contain active credentials or private victim data. A security dataset
can be externally validated and scientifically useful while deliberately using fictional
secrets. The relevant evidence is independent construction, annotation, peer review,
versioned release, and a frozen evaluation protocol.
