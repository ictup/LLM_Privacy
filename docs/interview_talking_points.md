# RAGShield Interview Talking Points

## 30-Second Summary

RAGShield is an auditable research prototype for measuring and reducing security
and privacy failures across RAG and tool-using LLM systems. I evaluated it on four
external peer-reviewed benchmarks: SafeRAG for malicious retrieved evidence,
Tensor Trust for direct hijacking and secret extraction, PrivacyLens for
contextual privacy in agent actions, and TAB for anonymization against human span
annotations. The results show that layered controls reduce attacks and leakage,
but also expose clear failures in semantic-noise detection, over-redaction, and
privacy-validator over-blocking.

## Presentation Structure

1. **Problem:** retrieved content and tool observations are untrusted data, but
   models can treat them as instructions or disclose them in later actions.
2. **Architecture:** tenant scope, context screening/redaction, untrusted-context
   boundary, model generation, output privacy validation, tool gate, and
   secret-safe audit.
3. **Experimental design:** frozen external data, paired systems, complete-case
   analysis, deterministic or structured scoring, confidence intervals, and
   public audits without raw benchmark text.
4. **Results:** present SafeRAG, Tensor Trust, PrivacyLens, and TAB as separate
   tasks rather than pooling incompatible metrics.
5. **Failures and PhD direction:** semantic provenance, validator calibration,
   adaptive attacks, and independent evaluation.

## Four Evidence Layers

### 1. SafeRAG: Indirect Retrieval Attacks

- ACL 2025 benchmark; 377 complete paired confirmatory cases.
- GPT-5 mini generated all three conditions and provided structured judgments.
- Attack adoption: 71.4% baseline, 40.6% context boundary, 29.7% full.
- Full versus baseline: -41.6 percentage points, 95% paired CI -47.7 to
  -35.8, exact McNemar `p < 0.0001`.
- Utility-F1 difference was inconclusive.
- Main failure: Silver Noise improved only 7.1 points.

### 2. Tensor Trust: Direct Hijacking and Extraction

- ICLR 2024 benchmark; fixed 100-case sample, 600 DeepSeek Flash calls.
- Attack success: 57% baseline, 35% context boundary, 0% final full system.
- Valid-access success: 61%, 87%, and 80%, respectively.
- Critical qualification: full raw model attack success was 36%; the final zero
  came from deterministic authorization and secret-output gating.

### 3. PrivacyLens: Contextual Privacy

- NeurIPS 2024 dataset; source-stratified 50-case sample.
- 100 generations, 100 privacy validations, and 400 Flash/Pro judge calls.
- Leakage/helpfulness: baseline 56%/94%, privacy prompt 14%/94%, output
  validator 14%/58%, full 6%/80%.
- The privacy prompt was the best measured trade-off; the validator alone
  over-blocked 42% of actions.
- Judges are different models from one provider, not human ground truth.

### 4. TAB: Human-Annotated Anonymization

- Computational Linguistics 2022 benchmark; full official test split of 127
  public ECHR documents and 7,248 protected mentions.
- Combined detector: 0.610 character F1, 0.674 full-coverage recall, 0.783 text
  retention, and 0.107 false-positive character rate.
- Main failure: person recall was 37.5% and miscellaneous-entity recall 14.1%.

## Questions to Answer Directly

**Did real LLMs run?**

Yes. The SafeRAG study used a pinned GPT-5 mini snapshot. Tensor Trust and
PrivacyLens used 1,200 successful DeepSeek response IDs in total. TAB is an
offline detector study and makes no LLM calls. The integrated tool/tenant
regression is deterministic and must not be described as a real-model benchmark.

**Are the datasets real?**

They are external, versioned, peer-reviewed research benchmarks. TAB contains
real public court text with human annotations. Tensor Trust contains attacks from
human players. SafeRAG is an author-released security benchmark. PrivacyLens uses
realistic constructed scenarios grounded in regulations, literature, and
crowdsourcing; it does not contain private victim records.

**Did the defense see the answers?**

No for the new pilots. Tensor Trust scoring uses access codes only after model
generation. PrivacyLens sensitive-item labels are withheld from generation and
output validation and supplied only to the automatic judges. Frozen sample IDs
and protocol files were committed before the paid runs.

**Why are there controlled fixtures?**

External benchmarks support the empirical claims. Small fixtures test
deterministic properties that benchmarks do not cover directly: tenant filtering
before ranking, role-based tool denial, high-risk fail-closed behavior, secret
redaction, and raw-value-free audit logs. They are regression tests, not a
synthetic benchmark.

**Why was the author-generated corpus removed?**

It was useful for early debugging but weak as independent evidence. The final
release relies on external peer-reviewed benchmarks for empirical claims and
retains only small deterministic fixtures for security regression.

**Which result is most important?**

The strongest scientific result is not a single lowest number. It is the paired
evidence that different layers solve different failures: context boundaries help
without blocking, hard output gates can eliminate residual attacks but reduce
utility, and semantic noise remains difficult for rules.

**What is the PhD research direction?**

Replace hand-engineered screening with learned provenance and semantic-conflict
models; optimize validators for the privacy-utility frontier; evaluate adaptive
attacks across retrieval and tools; and validate endpoints with independent
providers, repeated runs, and human labels.

## Claims to Avoid

- Do not say RAGShield solves prompt injection or is production secure.
- Do not describe Tensor Trust's final zero as model-level robustness.
- Do not call PrivacyLens automatic judgments human ground truth.
- Do not pool the four benchmarks into one effectiveness percentage.
- Do not present controlled tool/tenant fixtures as population-level evidence.
- Do not claim differential privacy, federated learning, or homomorphic encryption.
