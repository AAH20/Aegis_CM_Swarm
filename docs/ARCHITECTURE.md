# Aegis detection and remediation engineering architecture

## Trust boundary

Aegis separates probabilistic reasoning from privileged execution. Agents may research,
correlate, challenge, and propose. Typed deterministic services validate evidence, compile
detections, calculate dependency impact, enforce approval policy, and write outcome receipts.
No model response is itself authorization.

## Pipeline

1. A versioned security intent describes behaviors, evidence, sequence, and response policy.
2. Source adapters normalize observations without discarding original provenance.
3. The evidence engine builds a graph and may abstain when required evidence is absent.
4. Compilers produce backend detections with a shared semantic fingerprint.
5. The remediation planner evaluates reversibility and critical-service dependencies.
6. A human approval boundary precedes every action in the initial release.
7. An outcome receipt binds inputs, verdict, generated artifacts, and execution count.

## Initial vertical slice

The identity-intrusion pack correlates a suspicious session, remote-management execution,
persistence, and lateral movement. It emits SPL, KQL, ES|QL, and Sigma representations and
blocks high-risk containment when the target supports a critical service.

## Extension points

- OCSF/ECS normalization and immutable original-event storage.
- Splunk, QRadar, Elastic, Sentinel, Snort, Zeek, and osquery adapters.
- Durable workflow and approval services.
- EvidenceForge replay and adversarial mutation.
- Signed detection-as-code pull requests and canary promotion.
- Federated, privacy-preserving outcome benchmarks.

## Authority Mesh vertical slice

The `aegis.authority` module adds an execution-independent authority graph. It groups routes by
target and effect, measures enforcement coverage, detects equivalent-effect bypasses, and flags
reusable credentials that carry standing privileged authority. A decision proof binds the human
sponsor, agent, route, operation, target, canonical argument digest, policy generation, resource
state precondition, expiry, and nonce. The first fixture models the direct GitLab API route from
`Aegis_CM_Swarm2` alongside a governed MCP adapter. It performs no external side effect.
