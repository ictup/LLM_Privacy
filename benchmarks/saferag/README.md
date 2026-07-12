# SafeRAG Integration

RAGShield evaluates its final real-model protocol on **SafeRAG: Benchmarking
Security in Retrieval-Augmented Generation of Large Language Model**, published
as an ACL 2025 Long Paper (DOI: `10.18653/v1/2025.acl-long.230`).

## Provenance

- Upstream repository: `IAAR-Shanghai/SafeRAG`
- Pinned commit: `e8f579743b23e0a3937076dcc0792fe29027cba3`
- Dataset size: 387 Chinese RAG security cases
- Tasks: ICC, SA, SN, and WDoS
- Local manifest: [manifest.json](manifest.json)

The pinned upstream repository does not contain an explicit redistribution
license. RAGShield therefore stores no raw benchmark text in Git. Downloaded
files live under `data/external/saferag/`, which is ignored.

## Fetch and Verify

```powershell
py scripts\fetch_saferag.py
```

The fetcher downloads the dataset and four knowledge bases directly from the
authors, then verifies their SHA-256 hashes against the pinned manifest.

## Final Protocol

The frozen protocol is documented in
[../../docs/saferag_gpt5mini_protocol.md](../../docs/saferag_gpt5mini_protocol.md).
It uses eight fixed development cases and 379 confirmatory cases. The primary
analysis contains 377 complete paired cases across baseline, context-boundary,
and full RAGShield conditions.

Run a no-cost protocol check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_saferag_gpt5mini_study.ps1 `
  -Phase dry-run
```

Run or resume the study:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_saferag_gpt5mini_study.ps1
```

Final aggregate results are published in
[../../reports/saferag_gpt5mini_report.md](../../reports/saferag_gpt5mini_report.md).
Raw answers and blind-review material remain local.
