# AI agent security architecture roadmap

This is an implementation roadmap for engineers securing autonomous agents, MCP servers, A2A
workflows, Kubernetes workloads, and privileged tools. It is not a promise that reading a roadmap
confers seniority. Each completed stage requires code, adversarial tests, and independently
inspectable evidence.

## Stage 1: Separate reasoning from authority — implemented

An LLM may propose or enrich an action. It must not declare evidence, approve itself, or treat
model confidence as authorization.

Evidence:

- Typed evidence graph with abstention.
- Dependency-aware remediation planning.
- Deterministic decision boundary.
- Zero production actions in reference runs.

Run: `make identity-demo`

## Stage 2: Model identity and every privileged path — implemented

Inventory the human sponsor, agent, child agents, workload identity, credentials, protocols,
tools, backend targets, effects, and enforcement points. Group paths by equivalent effect rather
than tool name: two different tools may mutate the same resource.

Evidence:

- Standing privileged credential detection.
- Per-effect enforcement coverage.
- Governed versus ungoverned route discovery.
- Proof-bound action envelope.

Run: `make authority-demo`

## Stage 3: Reconcile decisions with external effects — implemented

Observe the resource independently. Join its state transition to the authority decision and
classify missing decisions, effects after denial, shadow paths, argument drift, actor substitution,
stale state, duplicates, and agent self-reporting.

Run: `make effects-demo`

## Stage 4: Establish cryptographic workload and sensor identity — next

- SPIFFE/SPIRE identities for agents, enforcement points, and observers.
- Short-lived proof-of-possession credentials.
- KMS-backed asymmetric receipts with rotation.
- Persistent nonce and replay protection.
- MCP tool-call attestation conformance vectors aligned with
  [MCP #2787](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2787).

Exit criterion: an offline verifier rejects a forged observer, modified request, stale key,
expired decision, and replayed effect across two independent implementations.

## Stage 5: Deploy live effect sensors

- PostgreSQL audit/logical-decoding adapter.
- Kubernetes audit and workload-event adapter.
- Envoy authorization metadata adapter.
- GitLab audit adapter.
- Generic HTTP mutation adapter.

Exit criterion: reproduce the alternate PostgreSQL route reported in
[MCP #2848](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2848#issuecomment-5175717523)
and detect the resulting `effect_without_decision` from resource-side evidence.

## Stage 6: Export causal, vendor-neutral telemetry

- W3C trace-context linkage from inference to tool execution.
- Opaque decision, governance, and receipt references.
- Explicit evidence origin: agent, proxy, resource sensor, or attested observer.
- Bounded cardinality and no prompts, arguments, credentials, or policy bodies in metrics.

Upstream targets:

- [OpenTelemetry #309](https://github.com/open-telemetry/semantic-conventions-genai/issues/309)
- [OpenTelemetry #239](https://github.com/open-telemetry/semantic-conventions-genai/issues/239)
- [OpenTelemetry #386](https://github.com/open-telemetry/semantic-conventions-genai/issues/386)

## Stage 7: Continuous adversarial verification

Use the Aegis swarm as a safe purple-team harness for:

- Alternate MCP and direct API paths.
- Child-agent credential inheritance.
- Approval replay and at-most-once violations.
- Tool shadowing and compromised server identity.
- State changes between approval and execution.
- Cross-server sensitive-data flow.
- Forged success, denial, and observer telemetry.

Exit criterion: publish a versioned coverage report containing the attack corpus, expected
decision, observed effect, receipt verification result, latency, and false-denial rate.

## Evidence standard

Every capability should publish:

1. The threat and trust boundary.
2. A public upstream demand signal where one exists.
3. A safe reproduction.
4. Deterministic acceptance and rejection tests.
5. A machine-readable result.
6. Honest limitations and residual risk.

That evidence—not labels such as “elite,” “CISO-ready,” or “production-ready”—is the seniority
signal this project is designed to compound.
