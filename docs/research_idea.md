# One-Page Research Idea

## Title

Automated Red-Blue Teaming for Privacy Leakage and Prompt-Injection Defense in RAG-Enabled LLM Agents

## Problem

RAG and tool-using LLM agents expand the attack surface of LLM applications. User prompts, retrieved documents, vector-store ranking behavior, tenant metadata, and external tools can all become channels for prompt injection, privacy leakage, source poisoning, and unauthorized actions. Existing evaluation often tests model behavior in isolation, while practical RAG systems require end-to-end evaluation across retrieval, generation, tool control, and logging.

## Research Question

How can we automatically discover, measure, and mitigate privacy leakage and prompt-injection vulnerabilities in RAG-augmented, tool-using LLM agents deployed in adversarial environments?

## Method

The proposed method is a controlled red-blue evaluation pipeline:

1. Build a varied synthetic multi-tenant RAG corpus containing multiple enterprise document forms, public/internal/confidential records, poisoned uploads, fake PII, and fake secrets; report duplication and target-reference quality explicitly.
2. Generate structured adversarial tests for direct prompt injection, indirect prompt injection, sensitive information disclosure, system prompt leakage, tool misuse, retrieval poisoning, and cross-tenant leakage.
3. Implement a baseline RAG-agent system with retrieval, citations, and sandbox tools.
4. Add defense layers: context separation, retrieval sanitization, fake PII/secret redaction, output validation, least-privilege tool gating, tenant filtering, and audit traces.
5. Run ablation experiments to measure security-utility trade-offs under attack success rate, leakage rate, unauthorized tool-call rate, poisoned retrieval influence, benign QA success, and latency overhead.
6. Validate external generalization with pinned peer-reviewed benchmarks, beginning with SafeRAG, while preserving upstream task definitions, provenance, and native retrieval metrics.

## Expected Contribution

The expected contribution is a reproducible security evaluation artifact for RAG agents. It combines controlled synthetic diagnostics with peer-reviewed external benchmarks to expose vulnerabilities, compare defense layers, and produce audit traces for failure analysis. The artifact also identifies open research problems around source trust, tenant-aware retrieval, paraphrased leakage detection, and policy verification for tool-using agents.

## Fit to University of Turku Position

The project connects LLM privacy preservation and security hardening with automated vulnerability attack and defense. It builds on LLM systems, RAG, evaluation, and deployment experience while adding a concrete security-oriented research artifact focused on privacy leakage, prompt injection, retrieval poisoning, and least-privilege agentic tool execution.

## Limitations and Next Steps

The current artifact combines a deterministic synthetic benchmark with an offline SafeRAG retrieval evaluation. The SafeRAG trusted-source condition uses benchmark provenance labels and should be interpreted as an oracle-like upper bound. Future work should reproduce the official embedding, reranking, generation, and QuestEval settings; test multiple open and hosted LLMs; add PrivacyLens and AgentDojo; and report repeated runs with confidence intervals.
