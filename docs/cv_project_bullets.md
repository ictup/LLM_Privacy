# Repository-Supported Project Bullets

Keep the `research prototype` qualifier. These statements match the committed
evidence; they are not instructions to alter already-submitted application files.

**RAGShield: Auditable Security and Privacy Evaluation for RAG and LLM Agents**

- Built a reproducible red-blue evaluation prototype covering indirect retrieval
  attacks, direct prompt hijacking and extraction, contextual privacy leakage,
  anonymization, tenant isolation, and least-privilege tool controls.
- Implemented tenant-scoped retrieval, label-free context screening,
  conflict-preserving deduplication, sensitive-data redaction, untrusted-context
  separation, policy-aware output validation, fail-closed tool gating, and
  versioned secret-safe audits.
- Evaluated four external peer-reviewed benchmarks: 377 complete SafeRAG cases,
  the full 127-document TAB test split, a frozen 100-case Tensor Trust pilot, and
  a source-stratified 50-case PrivacyLens pilot.
- Reduced judge-assessed SafeRAG attack adoption from 71.4% to 29.7% (paired
  difference -41.6 points, 95% CI -47.7 to -35.8; exact McNemar `p < 0.0001`).
- Rejudged all 1,131 frozen SafeRAG answers with DeepSeek Pro; the independent
  provider reproduced a -38.2-point full-system effect, while moderate kappa
  (0.479) exposed automatic-judge uncertainty.
- On Tensor Trust, reduced final attack success from 57% to 0% with layered
  authorization/output gating while retaining 80% valid-access success; raw
  full-system model attack success remained 36%.
- On PrivacyLens, reduced conservative dual-model leakage from 56% to 14% using
  privacy instructions at unchanged 94% helpfulness; the full system reached 6%
  leakage and 80% helpfulness.
- Preserved reproducibility through pinned benchmark commits, frozen samples,
  resumable 32-worker runners, cost preflights, paired statistics, 3,231 DeepSeek
  response IDs, and public audits that exclude raw benchmark content.
- Documented negative results: a 98-case semantic Silver Noise defense produced
  no significant security gain and reduced utility; TAB
  over-redaction and person recall, Tensor Trust dependence on deterministic
  gates, and PrivacyLens output-validator over-blocking.

Short version:

**RAGShield** *(research prototype)*: Built an auditable layered security pipeline
and evaluated four peer-reviewed RAG/privacy benchmarks. Measured substantial
reductions in SafeRAG attack adoption, Tensor Trust hijacking/extraction, and
PrivacyLens contextual leakage, while reporting residual semantic-noise,
over-redaction, judge-validity, and security-utility limitations.
