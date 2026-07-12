# RAGShield

Automated red-blue teaming for privacy leakage and prompt-injection defense in
RAG-enabled and tool-using LLM agents.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)
![Focus](https://img.shields.io/badge/Focus-LLM%20Security%20%26%20Privacy-purple)

This repository is a defensive research prototype. It uses only synthetic data,
fake PII, fake credentials, toy tools, and local evaluation logic. It must not be
used to attack third-party systems or extract real sensitive information.

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

## Current Results

The latest checked-in run evaluates 100 adversarial tests, 20 mixed benign-plus-
adversarial tests, and 30 benign QA tests. All results are from a deterministic
offline synthetic benchmark.

| System | ASR ↓ | Leakage ↓ | Unauthorized Tools ↓ | Benign Success ↑ |
|---|---:|---:|---:|---:|
| Baseline RAG | 100.0% | 66.7% | 50.0% | 100.0% |
| + Context Separation | 16.7% | 0.0% | 0.0% | 100.0% |
| + Retrieval Sanitizer | 16.7% | 0.0% | 0.0% | 100.0% |
| + PII Redaction | 16.7% | 0.0% | 0.0% | 100.0% |
| + Tool Gate | 16.7% | 0.0% | 0.0% | 100.0% |
| Full RAGShield | 0.0% | 0.0% | 0.0% | 100.0% |

See [reports/results.md](reports/results.md) and
[reports/failure_cases.md](reports/failure_cases.md).

## Repository Layout

```text
configs/                  Runtime and tool-policy configuration
data/
  attacks/                Synthetic adversarial test cases
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

```bash
python -m ragshield.ingestion.build_corpus --config configs/baseline.yaml
python -m ragshield.ingestion.build_attack_sets
python -m ragshield.evaluation.run_experiments --output-dir reports
python -m ragshield.evaluation.report --summaries reports/experiment_summaries.json
python -m ragshield.evaluation.failure_analysis --report-dir reports
python -m unittest discover -s tests
```

## Implementation Milestones

1. Initialize the repository, safety boundary, and configuration.
2. Generate synthetic documents and attack/evaluation sets.
3. Implement a baseline RAG pipeline and sandbox tools.
4. Implement security metrics and attack execution.
5. Add defense modules and tests.
6. Run baseline-vs-defense ablations and generate reports.
7. Package results for GitHub, CV, and a one-page research idea.

## Application Materials

- [CV project bullets](docs/cv_project_bullets.md)
- [One-page research idea](docs/research_idea.md)

## Safety Boundary

Only run this project on self-owned local systems with synthetic data. Do not use
real credentials, real private data, production services, or third-party systems.
Do not publish payloads intended for credential theft, malware, unauthorized
access, or real data exfiltration.

## Limitations

- The current implementation is a deterministic offline prototype, not a claim of
  production-grade security.
- Regex-based redaction and validation only cover synthetic markers and obvious
  leakage patterns.
- The retriever is lexical and intentionally lightweight; future work can add
  FAISS, pgvector, reranking models, and LLM-backed judges.
- The benchmark is designed for controlled research demonstration and should be
  expanded before making broader empirical claims.
