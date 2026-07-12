# RAGShield

Automated red-blue teaming for privacy leakage and prompt-injection defense in
RAG-enabled and tool-using LLM agents.

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

## Minimal Workflow

```bash
python -m ragshield.ingestion.build_corpus --config configs/baseline.yaml
python -m ragshield.evaluation.attack_runner --config configs/baseline.yaml --attacks data/attacks/all.jsonl --output reports/baseline_results.jsonl
python -m ragshield.evaluation.attack_runner --config configs/ragshield_full.yaml --attacks data/attacks/all.jsonl --output reports/ragshield_results.jsonl
python -m ragshield.evaluation.report --baseline reports/baseline_results.jsonl --defense reports/ragshield_results.jsonl --output reports/results.md
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

## Safety Boundary

Only run this project on self-owned local systems with synthetic data. Do not use
real credentials, real private data, production services, or third-party systems.
Do not publish payloads intended for credential theft, malware, unauthorized
access, or real data exfiltration.
