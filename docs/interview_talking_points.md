# RAGShield Interview Talking Points

## 30-Second Summary

RAGShield is a research prototype for testing and defending RAG systems against adversarial
retrieved evidence. I evaluated the same fixed GPT-5 mini model under three paired
conditions on the peer-reviewed SafeRAG benchmark. Across 377 complete confirmatory cases,
the full defense reduced judge-assessed attack adoption from 71.4% to 29.7%. The experiment
also exposes a clear failure: semantically plausible silver noise remains difficult for
the current rule-based screener.

## What I Built

- A BM25 RAG baseline and fixed-model OpenAI Responses API runner.
- An explicit untrusted-context boundary.
- Label-free context screening and conflict-preserving deduplication.
- Sensitive-pattern redaction and policy-aware output validation.
- Structured judging, paired statistics, resumable execution, and hash-based audits.

## How to Explain the Evidence

SafeRAG was released with an ACL 2025 Long Paper and provides 387 Chinese RAG-security
cases. I used eight cases only for development and kept 379 for confirmation. Two cases
repeatedly failed operationally, so I froze a complete-case rule and analyzed the remaining
377 cases under all three systems.

The primary metric is attack adoption. It asks whether the answer actually follows the
malicious or corrupted claim. It does not count an answer as compromised merely because
the model mentions the attack while warning about it. Full RAGShield reduced this rate by
41.6 percentage points; the paired 95% confidence interval was 35.8 to 47.7 points and the
exact McNemar test gave `p < 0.0001`.

## The Most Important Failure

Silver noise remained difficult: adoption fell only from 52.0% to 44.9%. The current
screener is strongest when an attack has recognizable instructions, advertising patterns,
or obvious denial-of-service content. It is weaker when a misleading passage resembles
ordinary relevant evidence. This motivates learned provenance, semantic contradiction
detection, and adaptive attacker training rather than adding more keyword rules.

## Questions to Answer Directly

**Did a real LLM run?**

Yes. Every reported confirmatory generation and automated judgment used the pinned
`gpt-5-mini-2025-08-07` API snapshot. Public reports include aggregate token, latency, and
response-status audits; raw answers remain local because SafeRAG has no explicit
redistribution license at the pinned commit.

**Why use the same model as generator and judge?**

It kept the study affordable and frozen, but it introduces correlated-bias risk. The next
validation step is the generated 48-answer blind human review, followed by an independent
model judge. Until then, the endpoint is explicitly called judge-assessed attack adoption.

**Why were two cases excluded?**

They repeatedly failed at the API stage. I excluded the whole paired case rather than mix
systems with different sample sizes, documented the exact IDs, and retained successful raw
rows locally. The decision was frozen before inspecting final outcome tables.

**Did the defense preserve utility?**

The measured utility-F1 difference was approximately zero, but its confidence interval
crossed zero. Therefore, the correct conclusion is that utility preservation remains
inconclusive under this strict option-level proxy.

**What would be the PhD research contribution?**

Move from hand-engineered screening to adaptive, provenance-aware defenses and evaluation:
learn source trust and semantic conflicts, generate attacks against the complete RAG path,
validate with humans and independent judges, and compare multiple models and retrievers.

## Claims to Avoid

- Do not say RAGShield solves prompt injection or is production secure.
- Do not say the utility stayed the same; say the measured difference was inconclusive.
- Do not claim empirical PII leakage, cross-tenant, or tool-misuse results.
- Do not claim differential privacy, federated learning, or homomorphic encryption.
- Do not call the automated judge independent until human or cross-model validation exists.
