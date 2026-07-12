# RAGShield

Automated red-blue teaming for privacy leakage and prompt-injection defense in
RAG-enabled and tool-using LLM agents.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)
![Focus](https://img.shields.io/badge/Focus-LLM%20Security%20%26%20Privacy-purple)

This repository is a defensive research prototype. It uses controlled synthetic data
and pinned author-released research benchmarks, with fake PII, fake credentials, toy
tools, and local evaluation logic. It must not be used to attack third-party systems or
extract real sensitive information.

## Research Question

How can we automatically discover, measure, and mitigate privacy leakage and
prompt-injection vulnerabilities in RAG-augmented, tool-using LLM agents deployed
in adversarial environments?

## Scope

RAGShield evaluates a controlled toy RAG-agent system against:

- Direct prompt injection.
- Indirect prompt injection through retrieved documents.
- Sensitive information disclosure.
- System prompt leakage.
- Tool misuse and excessive agency.
- Retrieval poisoning.
- Cross-user and multi-tenant leakage.

The defense stack includes:

- Instruction hierarchy and untrusted-context boundaries.
- Retrieval sanitization.
- PII and secret redaction.
- Policy-aware output validation.
- Least-privilege tool-call authorization.
- Audit-friendly JSONL traces.

## Peer-Reviewed Benchmark Evaluation

RAGShield now includes an adapter for [SafeRAG](https://aclanthology.org/2025.acl-long.230/),
an ACL 2025 Long Paper benchmark containing 387 Chinese RAG security cases across soft
advertising (SA), inter-context conflict (ICC), silver noise (SN), and white denial of
service (WDoS).

| System | Retrieval Accuracy ↑ | Gold Hit ↑ | Attack Exposure ↓ | Attack Keyword Cases ↓ |
|---|---:|---:|---:|---:|
| Baseline lexical RAG | 52.9% | 95.3% | 89.1% | 86.4% |
| RAGShield trusted-source retrieval | 96.5% | 100.0% | 0.0% | 0.0% |

This is an offline architecture-level evaluation, not a reproduction of SafeRAG's
LLM-based QuestEval table. The defended condition uses clean/attack provenance supplied
by the benchmark, so it is an oracle-like trusted-source upper bound. Attack Keyword
Cases uses a top-two extractive response proxy and is not an LLM attack success rate.
See [the full SafeRAG report](reports/saferag_report.md) and
[integration notes](benchmarks/saferag/README.md).

The upstream repository has no explicit redistribution license at the pinned commit.
Raw files are therefore downloaded directly from the authors and excluded from this repo.

## Controlled Synthetic Results

The latest checked-in run evaluates 132 varied adversarial tests, 24 mixed benign-plus-
adversarial tests, and 48 benign QA tests against 240 fictional enterprise documents.
All results are from a deterministic offline synthetic benchmark.

| System | ASR ↓ | Leakage ↓ | Unauthorized Tools ↓ | Benign Success ↑ |
|---|---:|---:|---:|---:|
| Baseline RAG | 91.7% | 63.5% | 48.7% | 95.8% |
| + Context Separation | 37.8% | 20.5% | 5.8% | 95.8% |
| + Retrieval Sanitizer | 28.2% | 21.1% | 5.8% | 100.0% |
| + PII Redaction | 16.0% | 0.0% | 5.8% | 100.0% |
| + Tool Gate | 10.3% | 0.0% | 0.0% | 100.0% |
| Full RAGShield | 0.0% | 0.0% | 0.0% | 100.0% |

See [reports/results.md](reports/results.md) and
[reports/failure_cases.md](reports/failure_cases.md). Dataset diversity and target-reference
validation are reported in [reports/data_quality.md](reports/data_quality.md).

## Dataset v2

The corpus models policies, manager FAQs, clinical notes, lab summaries, runbooks,
incident reviews, meeting minutes, support tickets, finance memos, tool cards, and
untrusted external uploads. Records vary by topic, organization, tenant, date, owner,
document form, amounts, workflow details, and synthetic identifiers.

- 240 documents: 30 per domain across 8 domains and 32 source types.
- 132 attacks across 7 categories, plus 24 mixed and 48 benign cases.
- 100% exact text/query uniqueness across all splits.
- 77.5% normalized corpus uniqueness after IDs and numbers are removed.
- 152 referenced target documents validated with no missing references.

All organizations, people, records, identifiers, credentials, and incidents are fictional.

## Repository Layout

```text
configs/                  Runtime and tool-policy configuration
benchmarks/               External benchmark manifests and integration notes
data/
  attacks/                Synthetic adversarial test cases
  external/               Downloaded, Git-ignored benchmark data
  eval_sets/              Benign and mixed QA test sets
  synthetic_docs/         Synthetic documents with metadata
src/ragshield/
  agents/                 Toy tools and tool authorization gate
  defenses/               Redaction, validation, context boundaries
  evaluation/             Attack runner, metrics, reports
  generation/             Prompts and deterministic answerer
  ingestion/              Corpus generation and chunking
  retrieval/              Vector-store-like lexical retrieval
  tracing/                JSONL audit logger
reports/                  Generated experiment outputs
scripts/                  Reproducible external benchmark fetchers
tests/                    Unit tests
```

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests
```

If you do not install the package, set `PYTHONPATH=src` before running modules.

## Reproduce the Benchmark

SafeRAG architecture evaluation:

```bash
python scripts/fetch_saferag.py
python -m ragshield.evaluation.run_saferag
```

Controlled synthetic benchmark:

```bash
python -m ragshield.ingestion.build_corpus --config configs/baseline.yaml
python -m ragshield.ingestion.build_attack_sets
python -m ragshield.evaluation.data_quality
python -m ragshield.evaluation.run_experiments --output-dir reports
python -m ragshield.evaluation.report --summaries reports/experiment_summaries.json
python -m ragshield.evaluation.failure_analysis --report-dir reports
python -m unittest discover -s tests
```

Real OpenAI model pilot on SafeRAG (16 paid API calls at the default two cases per task):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_saferag_llm_pilot.ps1
```

The script requests a newly created API key using hidden terminal input and keeps it only
in the child process environment. It records response IDs, resolved model names, token
usage, latency, and model answers. This controlled generation test uses labeled SafeRAG
contexts and the paper's attack-keyword formula, but it does not claim to reproduce the
paper's BM25 retrieval or LLM-based QuestEval results.

## Implementation Milestones

1. Initialize the repository, safety boundary, and configuration.
2. Generate synthetic documents and attack/evaluation sets.
3. Implement a baseline RAG pipeline and sandbox tools.
4. Implement security metrics and attack execution.
5. Add defense modules and tests.
6. Run baseline-vs-defense ablations and generate reports.
7. Package results for GitHub, CV, and a one-page research idea.
8. Integrate pinned peer-reviewed benchmarks with provenance and integrity checks.

## Application Materials

- [CV project bullets](docs/cv_project_bullets.md)
- [One-page research idea](docs/research_idea.md)

## Safety Boundary

Only run this project on self-owned local systems with synthetic or author-released
research data, following the source terms and without unauthorized redistribution. Do not
commit credentials, use real private data, or target unauthorized third-party systems.
Do not publish payloads intended for credential theft, malware, unauthorized
access, or real data exfiltration.

## Limitations

- The current implementation is a deterministic offline prototype, not a claim of
  production-grade security.
- Regex-based redaction and validation cover the benchmark's synthetic marker families
  and selected paraphrases, not arbitrary real-world sensitive data.
- The retriever is lexical and intentionally lightweight; future work can add
  FAISS, pgvector, reranking models, and LLM-backed judges.
- Scenario v2 is structurally more varied than the original template corpus, but remains
  deterministic and author-generated; broader empirical claims require external datasets,
  stronger retrievers, multiple LLMs, and adaptive attacks.
