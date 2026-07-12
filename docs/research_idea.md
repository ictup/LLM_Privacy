# One-Page Research Idea

## Title

RAGShield: Auditable Attack-and-Defense Evaluation for Adversarial RAG

## Problem

Retrieval-augmented generation expands the model's security boundary to include external
documents, source ranking, and conflicting evidence. Retrieved text can inject instructions,
promote unsupported claims, suppress useful answers, or introduce plausible but misleading
content. A defense that succeeds on a hand-written demonstration may still fail when the
attack resembles ordinary evidence or when defensive filtering removes useful context.

## Research Question

Can lightweight, provenance-aware controls reduce attack adoption in adversarial RAG
pipelines while preserving useful answers, and how can that effect be measured
reproducibly?

## Implemented Method

RAGShield compares three paired conditions: an undefended BM25 RAG baseline, the same
retrieved evidence wrapped in an explicit untrusted-context boundary, and a full condition
that adds label-free context screening, conflict-preserving deduplication,
sensitive-pattern redaction, and output validation.

The ACL 2025 SafeRAG benchmark supplies 387 Chinese security cases across inter-context
conflict, soft advertising, silver noise, and white denial of service. Eight cases were
fixed for development, leaving 379 untouched confirmatory cases. A pinned GPT-5 mini
snapshot generated and structured-judged all three conditions. The protocol records model
snapshots, response identifiers, completion status, token usage, latency, context hashes,
and judge outputs. Primary inference uses paired bootstrap confidence intervals and exact
McNemar tests. Attack adoption is separated from merely mentioning an injected claim while
warning about it.

## Current Evidence

Of 379 confirmatory SafeRAG cases, 377 produced complete generation and judgment rows for
all three systems. Full RAGShield reduced judge-assessed attack adoption from 71.4% to
29.7%, a paired reduction of 41.6 percentage points (95% CI: 35.8-47.7 points; exact
McNemar `p < 0.0001`). Utility F1 changed by 0.001 (95% CI: -0.023 to 0.024), so the run
does not establish a utility gain or loss. Performance varied sharply by attack family:
WDoS improved by 84.4 points, while silver noise improved by only 7.1 points.

## Research Contribution and Next Step

The contribution is an executable, auditable experimental artifact that connects an
external peer-reviewed benchmark to explicit defenses, paired measurements, and negative
results. It does not claim that prompt injection is solved. The strongest next direction
is to replace rule-based screening with learned provenance and semantic-conflict models,
then test adaptive attacks, multiple generator families, independent judges, repeated
stochastic runs, and blinded human labels.

## Fit to the University of Turku Position

The work directly addresses security hardening and automated vulnerability
attack-and-defense for LLM systems. It provides a concrete starting point for doctoral
research on secure retrieval, adversarial evidence, evaluation validity, and the
interaction between RAG defenses and broader privacy-preserving methods.
