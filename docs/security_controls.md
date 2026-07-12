# Controlled Security Extensions

RAGShield's empirical evidence uses SafeRAG, TAB, Tensor Trust, and PrivacyLens.
The controls in this document form a deterministic, side-effect-free regression
path. Their tests establish implementation behavior, not general security effectiveness.

## Security Path

```mermaid
flowchart LR
    U[Authenticated user] --> T[Tenant-scoped retrieval]
    T --> C[Attack screening and context redaction]
    C --> B[Untrusted-context boundary]
    B --> M[LLM generation]
    M --> P[PII, secret, and canary guard]
    P --> G[Least-privilege tool gate]
    G --> H[Fail-closed high-risk hold]
    H --> A[Secret-safe JSONL audit]
```

## Implemented Controls

| Control | Enforced behavior | Reported measure |
|---|---|---|
| Privacy guard | Detects controlled-test PII, secrets, account IDs, and system-prompt canaries; returns redacted text and hashed findings | Output leakage rate and finding counts by category/rule |
| Context defense | Screens explicit retrieved instructions, redacts controlled secrets, and marks retained chunks as untrusted | Removed/redacted context counts and boundary status |
| Tool gate | Denies unknown tools and unauthorized roles; high-risk exports require request-scoped, expiring approval | Unauthorized tool-call rate and decisions by reason |
| Tenant isolation | Derives scope from the authenticated principal and filters documents before scoring | Cross-tenant query and chunk exposure rates |
| Security audit | Records sequenced retrieval, privacy, tool, and metric events without raw prompts, outputs, secrets, or arguments | Versioned JSONL trace completeness |

The tools are controlled simulators. `send_email` and `export_records` never create an
external side effect. This keeps the demonstration safe and makes authorization tests
deterministic.

## Run the Demonstration

After installing the project, run:

```powershell
$env:PYTHONPATH = "src"
py scripts\run_security_controls_demo.py
```

The command writes local artifacts under `tmp/security_controls_demo/`, which is ignored
by Git. To regenerate the committed aggregate evidence, add
`--results-output reports/security_controls_results.json --report-output
reports/security_controls_report.md`. The summary labels itself
`deterministic_control_validation_not_an_llm_benchmark` to prevent confusion with the
external benchmark evidence.

## Claim Boundary

The implementation supports claims that these controls exist, compose into one pipeline,
fail closed in the tested cases, and produce secret-safe audit records. The regression
performs no human review or external tool side effect. It does not support claims about
population-level leakage reduction, production security, adaptive attackers, or
model-family generalization.
