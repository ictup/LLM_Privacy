# One-Page Research Idea

## Title

RAGShield: Auditable Attack-and-Defense Evaluation for Privacy-Aware RAG Agents

## Problem

RAG and tool-using LLM agents expand the security boundary beyond the language model.
User prompts, retrieved documents, source ranking, tenant metadata, generated outputs, and
external tools can each become channels for prompt injection, sensitive-data disclosure,
retrieval poisoning, or unauthorized actions. A defense that succeeds on a hand-written
demo may still fail when the attack is semantically plausible or when security controls
degrade useful answers. The core research problem is therefore to evaluate the complete
RAG data and action path under paired, auditable conditions.

## Research Question

How can layered, provenance-aware controls reduce attack adoption and privacy leakage in
RAG agents while preserving useful task performance, and how should that trade-off be
measured reproducibly?

## Implemented Method

RAGShield implements three paired conditions: an undefended BM25 RAG baseline, the same
retrieved evidence wrapped in an explicit untrusted-context boundary, and a full stack
that adds label-free context screening, conflict-preserving deduplication, fake PII/secret
redaction, output validation, tenant filtering, and least-privilege tool gating.

The evaluation separates two kinds of evidence:

1. **External validity:** the ACL 2025 SafeRAG benchmark supplies 387 Chinese security
   cases across inter-context conflict, soft advertising, silver noise, and white denial
   of service. Eight cases were used for development, leaving 379 untouched confirmatory
   cases. A fixed GPT-5 mini snapshot generated and structured-judged all conditions.
2. **Component validity:** an author-generated corpus supplies fake secrets, explicit
   tenant canaries, poisoned documents, and toy-tool requests. These deterministic markers
   test whether specific controls actually block the behavior they are designed to stop.

The protocol records model snapshots, response identifiers, status, tokens, latency,
context hashes, and judge outputs. Primary inference uses paired bootstrap confidence
intervals and exact McNemar tests. Attack adoption is distinguished from merely mentioning
an injected claim while warning about it.

## Current Evidence

Of 379 confirmatory SafeRAG cases, 377 produced complete generation and judgment rows for
all three systems. Full RAGShield reduced judge-assessed attack adoption from 71.4% to
29.7%, a paired reduction of 41.6 percentage points (95% CI: 35.8-47.7 points; exact
McNemar `p < 0.0001`). Utility-F1 changed by 0.001 (95% CI: -0.023 to 0.024), so the run
does not establish a utility gain or loss. Performance varied sharply by attack family:
WDoS improved by 84.4 points, while SN improved by only 7.1 points.

In the separate controlled canary study, the full stack produced no measured leakage,
unauthorized tool calls, poisoned-retrieval influence, or aggregate attack successes over
156 adversarial cases, with 97.9% success on 48 benign cases. This supports component
correctness under known markers, not robustness to arbitrary attacks.

## Research Contribution and Next Step

The current contribution is not a claim of a solved security problem. It is an executable,
auditable experimental artifact that connects attack taxonomies to concrete controls,
paired measurements, and failure analysis. The strongest next research direction is to
replace rule-based source screening with learned provenance and conflict models, then test
adaptive attacks, multiple generator families, an independent judge, repeated stochastic
runs, and blinded human labels. Privacy-preserving learning mechanisms can then be studied
as an additional layer; they are not part of the current evidence.

## Fit to the University of Turku Position

The work directly addresses the position's security-hardening and automated vulnerability
attack-and-defense themes. It provides a concrete starting point for doctoral research on
how privacy and security controls interact across retrieval, generation, and agent actions,
while making its present limits explicit.
