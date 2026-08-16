from __future__ import annotations

from dataclasses import dataclass

from .compilers import CompiledDetection, compile_detection
from .evidence import EvidenceGraph, build_evidence_graph, evaluate_intent
from .models import DetectionIntent, Finding, RemediationAction, SecurityEvent
from .receipts import OutcomeReceipt, create_receipt
from .remediation import DependencyGraph, plan_remediation


@dataclass(frozen=True)
class RuntimeResult:
    graph: EvidenceGraph
    finding: Finding
    detections: tuple[CompiledDetection, ...]
    remediation_plan: tuple[RemediationAction, ...]
    receipt: OutcomeReceipt

    def to_dict(self) -> dict:
        return {
            "finding": self.finding.to_dict(),
            "detections": [item.to_dict() for item in self.detections],
            "remediation_plan": [item.to_dict() for item in self.remediation_plan],
            "receipt": self.receipt.to_dict(),
        }


class AegisRuntime:
    """Deterministic control plane; model-based agents may enrich but never override it."""

    def run(
        self,
        intent: DetectionIntent,
        events: list[SecurityEvent],
        dependencies: DependencyGraph,
        backends: tuple[str, ...],
        target: str,
        signing_key: str | None = None,
    ) -> RuntimeResult:
        graph = build_evidence_graph(events)
        finding = evaluate_intent(intent, graph)
        detections = tuple(compile_detection(intent, backend) for backend in backends)
        remediation = plan_remediation(intent, finding, dependencies, target)
        receipt_payload = {
            "intent": {"id": intent.intent_id, "version": intent.version},
            "event_ids": sorted(event.event_id for event in events),
            "verdict": finding.verdict.value,
            "confidence": finding.confidence,
            "detection_backends": list(backends),
            "remediation_statuses": [action.status for action in remediation],
            "production_actions_executed": 0,
        }
        return RuntimeResult(
            graph=graph,
            finding=finding,
            detections=detections,
            remediation_plan=remediation,
            receipt=create_receipt(receipt_payload, signing_key),
        )
