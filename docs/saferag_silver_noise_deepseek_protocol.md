# Frozen SafeRAG Silver Noise Semantic-Defense Protocol

## Research question

Can a label-blind semantic and provenance screen reduce SafeRAG Silver Noise
attack adoption without relying on benchmark annotations at inference time, and
what utility cost does it introduce relative to the existing RAGShield stack?

## Frozen protocol

- Protocol: `saferag-silver-noise-deepseek-semantic-v1`
- Protocol SHA-256: `37fba832f10790fe0ab6e35d4c4d930261185bbec294d2e76294d4a0e58a9ea6`
- Benchmark: SafeRAG, pinned repository commit recorded by the project loader
- Task: all 100 Silver Noise cases
- Split: 2 development cases and 98 confirmatory cases, fixed by the existing
  SafeRAG study split
- Initial retrieval: six contexts per case, consisting of three benchmark attack
  contexts and three clean BM25 contexts
- Concurrency: 32 workers
- Temperature: 0
- Thinking mode: disabled

## Systems

1. `baseline`: no RAGShield defense.
2. `context_boundary`: explicit untrusted-context separation.
3. `ragshield_full`: the existing deterministic screening, context boundary,
   PII/secret redaction, and output validation stack.
4. `semantic_provenance`: a label-blind semantic screen followed by context
   boundary, PII/secret redaction, conservative evidence synthesis, and output
   validation.

## Models and calls

- Semantic screen: DeepSeek V4 Flash, 100 calls.
- Answer generation: DeepSeek V4 Flash, 400 calls.
- Independent structured judge: DeepSeek V4 Pro, 400 calls.
- Total planned paid calls: 900.

The semantic screen receives only the question, six opaque document IDs, and the
document text. It does not receive benchmark labels, attack positions, candidate
options, golden references, or judge outputs. Attack and clean labels are used
only after screening to calculate diagnostic recall, retention, and precision.

## Outcomes

The primary security outcome is confirmatory attack-adoption rate. The main
paired comparison is `semantic_provenance` versus `ragshield_full`; the comparison
with `baseline` is secondary. Utility macro-F1, grounded-answer rate, refusal rate,
and average retained-context count are reported for every system. Paired bootstrap
intervals and exact McNemar tests are used for system comparisons.

Screening diagnostics are attack-context quarantine recall, clean-context
retention, quarantine precision, and mean quarantined contexts. These are
post-hoc diagnostics and are not exposed to the semantic verifier.

## Reproducibility and exclusions

Raw API response IDs, benchmark text, and generated answers remain local and are
not redistributed. Public artifacts contain hashes, token usage, aggregate
metrics, and per-case binary/utility outcomes. Failed calls abort the phase; a
rerun resumes only the missing calls. A confirmatory report is emitted only when
all four systems have both a generation and a judgment for all 98 confirmatory
cases.

This is a benchmark experiment with automatic model-based evaluation. It does
not establish human ground truth and should not be presented as a production
security guarantee.
