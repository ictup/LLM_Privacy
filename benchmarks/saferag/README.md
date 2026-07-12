# SafeRAG Integration

RAGShield integrates the dataset released with **SafeRAG: Benchmarking Security in
Retrieval-Augmented Generation of Large Language Model** (ACL 2025 Long Papers,
DOI: `10.18653/v1/2025.acl-long.230`).

The upstream repository does not contain a `LICENSE` file or explicit redistribution
terms at the pinned commit. For that reason, RAGShield does not redistribute the dataset.
Use the fetch script to obtain the files directly from the authors' repository:

```bash
python scripts/fetch_saferag.py
```

The integration is pinned to commit `e8f579743b23e0a3937076dcc0792fe29027cba3`.
The adapter verifies SHA-256 hashes for the dataset and four knowledge bases before a run.
Downloaded files are stored under `data/external/saferag/` and excluded from Git.

The current offline runner evaluates retrieval robustness and attack-keyword propagation.
It does not reproduce SafeRAG's LLM-based QuestEval scores. Results must therefore be
described as a RAGShield architecture-level evaluation on SafeRAG data, not a direct
reproduction of the paper's model table.
