from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .models import ValidationError, _required_string
from .receipts import OutcomeReceipt, create_receipt


PRIVILEGED_EFFECTS = {"create", "delete", "execute", "isolate", "publish", "revoke", "update"}


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class Credential:
    credential_id: str
    kind: str
    standing: bool
    scope: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Credential":
        return cls(
            credential_id=_required_string(value, "credential_id"),
            kind=_required_string(value, "kind"),
            standing=bool(value.get("standing", True)),
            scope=tuple(value.get("scope", ())),
        )


@dataclass(frozen=True)
class AuthorityPath:
    path_id: str
    agent_id: str
    human_sponsor: str
    protocol: str
    endpoint: str
    operation: str
    target: str
    effect: str
    credential_id: str
    enforcement_points: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AuthorityPath":
        return cls(
            path_id=_required_string(value, "path_id"),
            agent_id=_required_string(value, "agent_id"),
            human_sponsor=_required_string(value, "human_sponsor"),
            protocol=_required_string(value, "protocol"),
            endpoint=_required_string(value, "endpoint"),
            operation=_required_string(value, "operation"),
            target=_required_string(value, "target"),
            effect=_required_string(value, "effect"),
            credential_id=_required_string(value, "credential_id"),
            enforcement_points=tuple(value.get("enforcement_points", ())),
        )

    @property
    def effect_key(self) -> str:
        return f"{self.target}::{self.effect}"

    @property
    def protected(self) -> bool:
        return bool(self.enforcement_points)


@dataclass(frozen=True)
class ActionRequest:
    request_id: str
    path_id: str
    arguments: dict[str, Any]
    policy_id: str
    policy_generation: str
    state_precondition: str
    approved: bool
    expires_at: str
    nonce: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ActionRequest":
        return cls(
            request_id=_required_string(value, "request_id"),
            path_id=_required_string(value, "path_id"),
            arguments=dict(value.get("arguments", {})),
            policy_id=_required_string(value, "policy_id"),
            policy_generation=_required_string(value, "policy_generation"),
            state_precondition=_required_string(value, "state_precondition"),
            approved=bool(value.get("approved", False)),
            expires_at=_required_string(value, "expires_at"),
            nonce=_required_string(value, "nonce"),
        )


@dataclass(frozen=True)
class ProofEnvelope:
    request_id: str
    human_sponsor: str
    agent_id: str
    path_id: str
    operation: str
    target: str
    effect: str
    arguments_digest: str
    policy_id: str
    policy_generation: str
    state_precondition: str
    expires_at: str
    nonce: str
    envelope_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorityFinding:
    finding_type: str
    severity: str
    effect_key: str
    path_ids: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorityDecision:
    request_id: str
    decision: str
    reason: str
    path_id: str
    proof: ProofEnvelope

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["proof"] = self.proof.to_dict()
        return value


@dataclass(frozen=True)
class AuthorityAnalysis:
    coverage: dict[str, float]
    findings: tuple[AuthorityFinding, ...]
    decision: AuthorityDecision
    receipt: OutcomeReceipt

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage": self.coverage,
            "findings": [finding.to_dict() for finding in self.findings],
            "decision": self.decision.to_dict(),
            "receipt": self.receipt.to_dict(),
            "production_actions_executed": 0,
        }


@dataclass(frozen=True)
class AuthorityTopology:
    topology_id: str
    credentials: tuple[Credential, ...]
    paths: tuple[AuthorityPath, ...]
    request: ActionRequest

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AuthorityTopology":
        topology = cls(
            topology_id=_required_string(value, "topology_id"),
            credentials=tuple(Credential.from_dict(item) for item in value.get("credentials", ())),
            paths=tuple(AuthorityPath.from_dict(item) for item in value.get("paths", ())),
            request=ActionRequest.from_dict(value.get("request", {})),
        )
        topology.validate()
        return topology

    def validate(self) -> None:
        if not self.credentials or not self.paths:
            raise ValidationError("authority topology requires credentials and paths")
        credential_ids = [item.credential_id for item in self.credentials]
        path_ids = [item.path_id for item in self.paths]
        if len(set(credential_ids)) != len(credential_ids):
            raise ValidationError("credential_id values must be unique")
        if len(set(path_ids)) != len(path_ids):
            raise ValidationError("path_id values must be unique")
        unknown_credentials = {path.credential_id for path in self.paths} - set(credential_ids)
        if unknown_credentials:
            raise ValidationError(f"paths reference unknown credentials: {sorted(unknown_credentials)}")
        if self.request.path_id not in path_ids:
            raise ValidationError("request references an unknown path")


def analyze_authority(topology: AuthorityTopology, signing_key: str | None = None) -> AuthorityAnalysis:
    credentials = {item.credential_id: item for item in topology.credentials}
    paths = {item.path_id: item for item in topology.paths}
    grouped: dict[str, list[AuthorityPath]] = {}
    for path in topology.paths:
        grouped.setdefault(path.effect_key, []).append(path)

    coverage = {
        effect: round(sum(path.protected for path in effect_paths) / len(effect_paths), 4)
        for effect, effect_paths in sorted(grouped.items())
    }
    findings: list[AuthorityFinding] = []
    for effect, effect_paths in sorted(grouped.items()):
        protected = [path for path in effect_paths if path.protected]
        unprotected = [path for path in effect_paths if not path.protected]
        if protected and unprotected:
            findings.append(AuthorityFinding(
                finding_type="equivalent_effect_bypass",
                severity="critical",
                effect_key=effect,
                path_ids=tuple(path.path_id for path in effect_paths),
                rationale="the same privileged effect is reachable through both governed and ungoverned paths",
            ))
    for path in topology.paths:
        credential = credentials[path.credential_id]
        if credential.standing and path.effect in PRIVILEGED_EFFECTS:
            findings.append(AuthorityFinding(
                finding_type="standing_privileged_authority",
                severity="high",
                effect_key=path.effect_key,
                path_ids=(path.path_id,),
                rationale=f"{credential.kind} credential {credential.credential_id} is reusable for a privileged effect",
            ))

    request = topology.request
    path = paths[request.path_id]
    envelope_fields = {
        "request_id": request.request_id,
        "human_sponsor": path.human_sponsor,
        "agent_id": path.agent_id,
        "path_id": path.path_id,
        "operation": path.operation,
        "target": path.target,
        "effect": path.effect,
        "arguments_digest": _canonical_digest(request.arguments),
        "policy_id": request.policy_id,
        "policy_generation": request.policy_generation,
        "state_precondition": request.state_precondition,
        "expires_at": request.expires_at,
        "nonce": request.nonce,
    }
    proof = ProofEnvelope(**envelope_fields, envelope_digest=_canonical_digest(envelope_fields))
    if not path.protected:
        decision_value, reason = "deny", "privileged action path has no authoritative enforcement point"
    elif credentials[path.credential_id].standing:
        decision_value, reason = "deny", "standing credential must be exchanged for call-bound authority"
    elif not request.approved:
        decision_value, reason = "deny", "proof envelope is bound but human approval is absent"
    else:
        decision_value, reason = "allow", "call is protected, approved, ephemeral, and bound to exact effect"
    decision = AuthorityDecision(request.request_id, decision_value, reason, path.path_id, proof)
    receipt = create_receipt({
        "topology_id": topology.topology_id,
        "coverage": coverage,
        "finding_digests": [_canonical_digest(finding.to_dict()) for finding in findings],
        "decision": decision.to_dict(),
        "production_actions_executed": 0,
    }, signing_key)
    return AuthorityAnalysis(coverage, tuple(findings), decision, receipt)
