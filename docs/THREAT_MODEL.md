# Threat model

## Protected assets

- Original security evidence and provenance.
- Security intent and detection artifacts.
- Customer credentials, topology, and dependency data.
- Approval decisions and outcome receipts.

## Principal threats

- Prompt injection embedded in telemetry.
- Fabricated evidence or model-generated citations.
- Cross-tenant evidence leakage.
- Over-privileged tool credentials.
- Unsafe or irreversible remediation.
- Replay, duplicate execution, or approval bypass.
- Compromised adapters and dependency confusion.

## Initial controls

- The reference runtime does not pass raw telemetry to an LLM.
- Verdicts derive from typed evidence and may abstain.
- Agents cannot execute remediation.
- Every action requires human approval; high-risk actions affecting critical services are blocked.
- Receipts use canonical SHA-256 digests and optional HMAC authentication.
- Original event identifiers remain in every finding.

## Not yet production-ready

The implementation is a deterministic reference vertical slice. Production deployments also
require tenant isolation, durable storage, KMS-backed signing, real adapter authentication,
authorization policy, idempotency, rate limits, external security testing, and an incident-
response procedure.
