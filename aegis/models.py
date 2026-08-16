from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ValidationError(ValueError):
    """Raised when an intent or evidence object violates the Aegis contract."""


class Verdict(str, Enum):
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ActionRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IRREVERSIBLE = "irreversible"


@dataclass(frozen=True)
class EvidenceRequirement:
    source: str
    event_type: str
    required_fields: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EvidenceRequirement":
        return cls(
            source=_required_string(value, "source"),
            event_type=_required_string(value, "event_type"),
            required_fields=tuple(value.get("required_fields", ())),
        )


@dataclass(frozen=True)
class DetectionIntent:
    intent_id: str
    name: str
    version: str
    description: str
    mitre_techniques: tuple[str, ...]
    evidence_requirements: tuple[EvidenceRequirement, ...]
    sequence: tuple[str, ...]
    window_minutes: int
    min_confidence: float
    remediation_actions: tuple[str, ...]
    protected_services: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DetectionIntent":
        intent = cls(
            intent_id=_required_string(value, "intent_id"),
            name=_required_string(value, "name"),
            version=_required_string(value, "version"),
            description=_required_string(value, "description"),
            mitre_techniques=tuple(value.get("mitre_techniques", ())),
            evidence_requirements=tuple(
                EvidenceRequirement.from_dict(item)
                for item in value.get("evidence_requirements", ())
            ),
            sequence=tuple(value.get("sequence", ())),
            window_minutes=int(value.get("window_minutes", 30)),
            min_confidence=float(value.get("min_confidence", 0.8)),
            remediation_actions=tuple(value.get("remediation_actions", ())),
            protected_services=tuple(value.get("protected_services", ())),
        )
        intent.validate()
        return intent

    def validate(self) -> None:
        if not self.mitre_techniques:
            raise ValidationError("intent must identify at least one MITRE technique")
        if not self.evidence_requirements or not self.sequence:
            raise ValidationError("intent requires evidence requirements and a sequence")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValidationError("min_confidence must be between 0 and 1")
        if self.window_minutes <= 0:
            raise ValidationError("window_minutes must be positive")
        known_types = {requirement.event_type for requirement in self.evidence_requirements}
        unknown = set(self.sequence) - known_types
        if unknown:
            raise ValidationError(f"sequence references unknown event types: {sorted(unknown)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SecurityEvent:
    event_id: str
    timestamp: str
    source: str
    event_type: str
    actor: str
    target: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SecurityEvent":
        return cls(
            event_id=_required_string(value, "event_id"),
            timestamp=_required_string(value, "timestamp"),
            source=_required_string(value, "source"),
            event_type=_required_string(value, "event_type"),
            actor=_required_string(value, "actor"),
            target=_required_string(value, "target"),
            attributes=dict(value.get("attributes", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Finding:
    verdict: Verdict
    confidence: float
    supporting_event_ids: tuple[str, ...]
    contradicting_event_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    matched_sequence: tuple[str, ...]
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["verdict"] = self.verdict.value
        return value


@dataclass(frozen=True)
class RemediationAction:
    action_id: str
    adapter: str
    operation: str
    target: str
    risk: ActionRisk
    reversible: bool
    preconditions: tuple[str, ...]
    rollback: str
    status: str = "proposed"
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["risk"] = self.risk.value
        return value


def _required_string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValidationError(f"{key} must be a non-empty string")
    return result
