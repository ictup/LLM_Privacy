# RAGShield Integrated Security-Control Regression

## Scope

This is a deterministic, side-effect-free system regression using controlled fixtures. It proves that the implemented controls compose and fail closed in these cases; it is not an external benchmark or a population-level security claim.

## Results

| Layer | Open/baseline | Integrated RAGShield |
|---|---:|---:|
| Cross-tenant query exposure | 100.0% | 0.0% |
| Controlled output leakage | 50.0% | 0.0% |
| Contexts removed | 0 | 1 / 3 |
| Contexts redacted | 0 | 1 / 2 |
| Denied tool requests | 0 | 1 |
| High-risk requests held | 0 | 1 |

## End-to-End Checks

- [x] `tenant_filter_prevents_cross_tenant_exposure`
- [x] `context_attack_removed`
- [x] `context_secret_redacted`
- [x] `untrusted_boundary_applied`
- [x] `output_leakage_removed`
- [x] `unauthorized_tool_denied`
- [x] `high_risk_tool_fails_closed`
- [x] `audit_sequence_contiguous_per_trace`
- [x] `audit_contains_no_raw_control_values`

All checks passed: **True**

## Claim Boundary

The tenant, context, output, tool, and audit controls run in one request path. Tools are controlled simulators and create no email, export, or other external side effect. High-risk actions remain blocked without a scoped approval; this run performs no human review.
