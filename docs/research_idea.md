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

RAGShield composes tenant-scoped retrieval, label-free context screening,
conflict-preserving deduplication, sensitive-pattern redaction, explicit
untrusted-context boundaries, output privacy validation, least-privilege tool
gating, and secret-safe audits. Benchmark-specific ablations isolate context
boundaries, generation-time privacy instructions, and output enforcement.

The evaluation uses four external peer-reviewed benchmarks. SafeRAG measures
indirect retrieval attacks with a pinned GPT-5 mini snapshot. Tensor Trust tests
direct hijacking and secret extraction with deterministic scoring. PrivacyLens
tests contextual disclosure in agent actions with two DeepSeek automatic judges.
TAB evaluates anonymization against human span annotations. Protocols record
dataset commits, frozen samples, response identifiers, token usage, latency,
hashes, complete-case rules, paired bootstrap intervals, and exact McNemar tests.

## Current Evidence

- SafeRAG: attack adoption fell from 71.4% to 29.7% on 377 paired cases; a
  complete DeepSeek rejudge reproduced a 38.2-point paired reduction on the same
  answers, with moderate cross-judge agreement (kappa 0.479).
- Silver Noise follow-up: a label-blind semantic screen changed adoption from
  38.8% to 33.7%, but the effect was not significant and utility F1 fell from
  37.6% to 21.6%; the proposed semantic defense remains an open problem.
- Tensor Trust: attack success fell from 57% to 35% with context separation and
  to a final 0% with authorization/output gating on 100 paired cases; valid
  access was 80% in the full system.
- PrivacyLens: leakage fell from 56% to 14% with a privacy prompt at unchanged
  94% helpfulness; the full system reached 6% leakage and 80% helpfulness on 50
  paired cases.
- TAB: the combined detector reached 0.610 character F1 and 0.674 full-coverage
  recall on 127 documents, while retaining 78.3% of text.

## Research Contribution and Next Step

The contribution is an executable, auditable artifact that connects external
peer-reviewed benchmarks to explicit defenses, paired measurements, and negative
results. It does not claim that prompt injection or privacy leakage is solved.
The strongest next direction is learned provenance and semantic-conflict models,
privacy-validator calibration, adaptive end-to-end attacks, multiple model and
retriever families, repeated stochastic runs, and independent evaluation.

## Fit to the University of Turku Position

The work directly addresses security hardening and automated vulnerability
attack-and-defense for LLM systems. It provides a concrete starting point for doctoral
research on secure retrieval, adversarial evidence, evaluation validity, and the
interaction between RAG defenses and broader privacy-preserving methods.
