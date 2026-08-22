# Aegis Authority Mesh proof matrix

This matrix connects expensive, publicly raised agent-security problems to executable Aegis
controls. It distinguishes implemented evidence from planned work; a GitHub issue alone is not
treated as proof that Aegis solves it.

| Expensive problem | Public signal | Aegis status | Executable proof |
| --- | --- | --- | --- |
| A second MCP server reaches the same database and bypasses approval | [MCP #2848 field report](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2848#issuecomment-5175717523) | Implemented as a protocol-neutral equivalent-effect path | [`test_approved_call_through_different_path_is_shadow_effect`](../tests/test_effects.py) |
| Approval is not authority unless bound to the exact call | [MCP #2848](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2848) | Proof binds sponsor, agent, route, operation, target, arguments, policy generation, state, expiry, and nonce | [`ProofEnvelope`](../aegis/authority.py) |
| MCP cannot cryptographically prove which agent invoked which tool with which arguments | [MCP #2787](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2787) | Canonical request commitment implemented; interoperable asymmetric SEP vectors are planned | [`test_allows_protected_ephemeral_approved_path`](../tests/test_authority.py) |
| Tool authorization requires protocol-neutral extension points | [Kube Agentic Networking #308](https://github.com/kubernetes-sigs/kube-agentic-networking/issues/308) | Aegis decision contract is protocol-neutral; upstream proposal opened | [KAN PR #320](https://github.com/kubernetes-sigs/kube-agentic-networking/pull/320) |
| Authorization metadata must be observable at the enforcement point | [Kube Agentic Networking #170](https://github.com/kubernetes-sigs/kube-agentic-networking/issues/170) | Decision and receipt identifiers exist; live Envoy metadata export is planned | [`AuthorityDecision`](../aegis/authority.py) |
| Agent traces do not show which model output caused a tool execution | [OpenTelemetry #309](https://github.com/open-telemetry/semantic-conventions-genai/issues/309) | Causal OTel adapter planned | — |
| Governance records need safe decision join points | [OpenTelemetry #239](https://github.com/open-telemetry/semantic-conventions-genai/issues/239) | Opaque decision and receipt IDs implemented; SemConv exporter planned | [`OutcomeReceipt`](../aegis/receipts.py) |
| Governance telemetry may be self-reported rather than externally attested | [OpenTelemetry #386](https://github.com/open-telemetry/semantic-conventions-genai/issues/386) | Evidence origin and self-report rejection implemented; remote sensor attestation planned | [`test_self_reported_effect_is_not_trusted`](../tests/test_effects.py) |
| Cross-server data origin is lost during tool chains | [MCP #3193](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3193) | Data-flow effects planned | — |

## Verification boundary

The current repository proves deterministic classification and receipt commitments over supplied
observations. It does not yet prove that a remote observer is genuine. Production completion needs:

- SPIFFE or hardware-backed sensor identity.
- KMS-backed Ed25519/ECDSA signatures and key rotation.
- Replay storage and clock-skew enforcement.
- Live PostgreSQL, Kubernetes, GitLab, Envoy, MCP, and OpenTelemetry adapters.
- Cross-implementation canonicalization vectors.
- Durable, tenant-isolated decision and outcome storage.

That boundary is explicit so demonstrations cannot be mistaken for deployed assurance.
