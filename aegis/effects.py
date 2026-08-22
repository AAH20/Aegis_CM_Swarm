from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .authority import AuthorityAnalysis, AuthorityTopology, _canonical_digest, analyze_authority
from .models import ValidationError, _required_string
from .receipts import OutcomeReceipt, create_receipt


@dataclass(frozen=True)
class ObservedEffect:
    effect_id: str
    request_id: str | None
    observed_at: str
    observer_id: str
    observer_origin: str
    externally_verified: bool
    agent_id: str
    path_id: str
    operation: str
    target: str
    effect: str
    arguments_digest: str
    state_precondition: str
    state_before: str
    state_after: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ObservedEffect":
        request_id = value.get("request_id")
        if request_id is not None and (not isinstance(request_id, str) or not request_id.strip()):
            raise ValidationError("request_id must be null or a non-empty string")
        return cls(
            effect_id=_required_string(value, "effect_id"),
            request_id=request_id,
            observed_at=_required_string(value, "observed_at"),
            observer_id=_required_string(value, "observer_id"),
            observer_origin=_required_string(value, "observer_origin"),
            externally_verified=bool(value.get("externally_verified", False)),
            agent_id=_required_string(value, "agent_id"),
            path_id=_required_string(value, "path_id"),
            operation=_required_string(value, "operation"),
            target=_required_string(value, "target"),
            effect=_required_string(value, "effect"),
            arguments_digest=_required_string(value, "arguments_digest"),
            state_precondition=_required_string(value, "state_precondition"),
            state_before=_required_string(value, "state_before"),
            state_after=_required_string(value, "state_after"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReconciliationFinding:
    effect_id: str
    classification: str
    severity: str
    request_id: str | None
    decision_id: str | None
    rationale: str
    observed_by: str
    evidence_origin: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EffectReconciliation:
    authority: AuthorityAnalysis
    findings: tuple[ReconciliationFinding, ...]
    summary: dict[str, int]
    receipt: OutcomeReceipt

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority.to_dict(),
            "effect_findings": [finding.to_dict() for finding in self.findings],
            "summary": self.summary,
            "outcome_receipt": self.receipt.to_dict(),
            "production_actions_executed_by_aegis": 0,
        }


@dataclass(frozen=True)
class EffectScenario:
    scenario_id: str
    topology: AuthorityTopology
    observed_effects: tuple[ObservedEffect, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EffectScenario":
        raw_topology = value.get("authority_topology")
        if not isinstance(raw_topology, dict):
            raise ValidationError("authority_topology must be an object")
        raw_effects = value.get("observed_effects")
        if not isinstance(raw_effects, list) or not raw_effects:
            raise ValidationError("observed_effects must be a non-empty array")
        scenario = cls(
            scenario_id=_required_string(value, "scenario_id"),
            topology=AuthorityTopology.from_dict(raw_topology),
            observed_effects=tuple(ObservedEffect.from_dict(item) for item in raw_effects),
        )
        effect_ids = [item.effect_id for item in scenario.observed_effects]
        if len(set(effect_ids)) != len(effect_ids):
            raise ValidationError("effect_id values must be unique")
        return scenario


def reconcile_effects(scenario: EffectScenario, signing_key: str | None = None) -> EffectReconciliation:
    authority = analyze_authority(scenario.topology, signing_key)
    decision = authority.decision
    proof = decision.proof
    known_paths = {path.path_id: path for path in scenario.topology.paths}
    request_counts: dict[str, int] = {}
    for effect in scenario.observed_effects:
        if effect.request_id:
            request_counts[effect.request_id] = request_counts.get(effect.request_id, 0) + 1

    findings = tuple(
        _classify_effect(effect, decision.decision, proof, known_paths, request_counts)
        for effect in scenario.observed_effects
    )
    summary: dict[str, int] = {}
    for finding in findings:
        summary[finding.classification] = summary.get(finding.classification, 0) + 1

    receipt_payload = {
        "scenario_id": scenario.scenario_id,
        "authority_decision_digest": _canonical_digest(decision.to_dict()),
        "observed_effect_digests": [_canonical_digest(effect.to_dict()) for effect in scenario.observed_effects],
        "reconciliation_digests": [_canonical_digest(finding.to_dict()) for finding in findings],
        "summary": summary,
        "observer_ids": sorted({effect.observer_id for effect in scenario.observed_effects}),
        "all_effects_externally_verified": all(effect.externally_verified for effect in scenario.observed_effects),
        "production_actions_executed_by_aegis": 0,
    }
    return EffectReconciliation(authority, findings, summary, create_receipt(receipt_payload, signing_key))


def _classify_effect(
    effect: ObservedEffect,
    decision_value: str,
    proof: Any,
    known_paths: dict[str, Any],
    request_counts: dict[str, int],
) -> ReconciliationFinding:
    decision_id = proof.request_id if effect.request_id == proof.request_id else None
    path = known_paths.get(effect.path_id)
    if not effect.externally_verified:
        classification, severity, rationale = (
            "untrusted_effect_evidence", "high", "effect was self-reported or lacks external verification"
        )
    elif effect.request_id is None or decision_id is None:
        classification, severity, rationale = (
            "effect_without_decision", "critical", "external sensor observed a privileged effect with no matching decision"
        )
    elif decision_value != "allow":
        classification, severity, rationale = (
            "denied_but_effect_observed", "critical", "an external effect occurred after the matching request was denied"
        )
    elif effect.path_id != proof.path_id:
        classification, severity, rationale = (
            "effect_via_shadow_path", "critical", "approved effect was produced through a different execution path"
        )
    elif path is None or not path.protected:
        classification, severity, rationale = (
            "effect_via_shadow_path", "critical", "effect path is unknown or has no authoritative enforcement point"
        )
    elif effect.agent_id != proof.agent_id:
        classification, severity, rationale = (
            "authorized_but_actor_changed", "critical", "observed workload identity differs from the approved agent"
        )
    elif effect.target != proof.target or effect.effect != proof.effect or effect.operation != proof.operation:
        classification, severity, rationale = (
            "authorized_but_effect_changed", "critical", "observed target, effect, or operation differs from the approved envelope"
        )
    elif effect.arguments_digest != proof.arguments_digest:
        classification, severity, rationale = (
            "authorized_but_arguments_changed", "critical", "observed arguments do not match the approved commitment"
        )
    elif effect.state_precondition != proof.state_precondition:
        classification, severity, rationale = (
            "authorized_but_state_stale", "critical", "resource state no longer matches the approved precondition"
        )
    elif request_counts.get(effect.request_id or "", 0) > 1:
        classification, severity, rationale = (
            "authorized_but_duplicate", "critical", "more than one effect was observed for a single authorized request"
        )
    else:
        classification, severity, rationale = (
            "authorized_and_matched", "info", "external effect matches the approved call envelope"
        )
    return ReconciliationFinding(
        effect_id=effect.effect_id,
        classification=classification,
        severity=severity,
        request_id=effect.request_id,
        decision_id=decision_id,
        rationale=rationale,
        observed_by=effect.observer_id,
        evidence_origin=effect.observer_origin,
    )
