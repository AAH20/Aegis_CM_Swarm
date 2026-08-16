from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .models import DetectionIntent, Finding, SecurityEvent, Verdict


@dataclass(frozen=True)
class EvidenceGraph:
    events: tuple[SecurityEvent, ...]
    adjacency: dict[str, tuple[str, ...]]

    def to_dict(self) -> dict:
        return {
            "events": [event.to_dict() for event in self.events],
            "adjacency": self.adjacency,
        }


def build_evidence_graph(events: list[SecurityEvent]) -> EvidenceGraph:
    """Connect events sharing an actor or target while preserving source evidence."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for event in events:
        buckets[event.actor].append(event.event_id)
        buckets[event.target].append(event.event_id)

    adjacency: dict[str, set[str]] = {event.event_id: set() for event in events}
    for event_ids in buckets.values():
        for event_id in event_ids:
            adjacency[event_id].update(other for other in event_ids if other != event_id)
    return EvidenceGraph(
        events=tuple(sorted(events, key=lambda event: event.timestamp)),
        adjacency={key: tuple(sorted(value)) for key, value in adjacency.items()},
    )


def evaluate_intent(intent: DetectionIntent, graph: EvidenceGraph) -> Finding:
    """Evaluate connected, time-bounded sequences with contradiction and abstention."""
    components = _connected_components(graph)
    candidates = [_evaluate_component(intent, component) for component in components]
    if not candidates:
        return Finding(
            verdict=Verdict.INSUFFICIENT_EVIDENCE,
            confidence=0.0,
            supporting_event_ids=(),
            contradicting_event_ids=(),
            missing_evidence=intent.sequence,
            matched_sequence=(),
            rationale=("no evidence supplied", "automation abstains when evidence coverage is insufficient"),
        )
    return max(candidates, key=lambda finding: (finding.confidence, len(finding.supporting_event_ids)))


def _evaluate_component(intent: DetectionIntent, events: list[SecurityEvent]) -> Finding:
    ordered = sorted(events, key=lambda event: _timestamp(event.timestamp))
    required_by_type = {item.event_type: item for item in intent.evidence_requirements}
    matched: list[SecurityEvent] = []
    missing: list[str] = []
    cursor = 0

    for expected_type in intent.sequence:
        found = None
        for event in ordered[cursor:]:
            if event.event_type == expected_type:
                found = event
                cursor = ordered.index(event) + 1
                break
        if found is None:
            missing.append(expected_type)
        else:
            matched.append(found)

    if len(matched) > 1:
        elapsed_seconds = (_timestamp(matched[-1].timestamp) - _timestamp(matched[0].timestamp)).total_seconds()
        if elapsed_seconds > intent.window_minutes * 60:
            missing.append(f"sequence_outside_{intent.window_minutes}m_window")
            matched = [matched[0]]

    field_gaps: list[str] = []
    for event in matched:
        requirement = required_by_type[event.event_type]
        for field_name in requirement.required_fields:
            if field_name not in event.attributes:
                field_gaps.append(f"{event.event_type}.{field_name}")

    contradictory = tuple(
        event.event_id
        for event in ordered
        if event.attributes.get("known_benign") is True
    )
    missing.extend(field_gaps)
    coverage = len(matched) / len(intent.sequence)
    contradiction_penalty = min(0.4, 0.15 * len(contradictory))
    confidence = round(max(0.0, coverage - contradiction_penalty), 3)

    if missing and coverage < 0.75:
        verdict = Verdict.INSUFFICIENT_EVIDENCE
    elif confidence >= intent.min_confidence and not contradictory:
        verdict = Verdict.MALICIOUS
    elif confidence >= 0.5:
        verdict = Verdict.SUSPICIOUS
    else:
        verdict = Verdict.BENIGN

    rationale = (
        f"matched {len(matched)}/{len(intent.sequence)} required behaviors",
        f"observed {len(contradictory)} explicit benign-context contradictions",
        "automation abstains when evidence coverage is insufficient",
    )
    return Finding(
        verdict=verdict,
        confidence=confidence,
        supporting_event_ids=tuple(event.event_id for event in matched),
        contradicting_event_ids=contradictory,
        missing_evidence=tuple(sorted(set(missing))),
        matched_sequence=tuple(event.event_type for event in matched),
        rationale=rationale,
    )


def _connected_components(graph: EvidenceGraph) -> list[list[SecurityEvent]]:
    by_id = {event.event_id: event for event in graph.events}
    unseen = set(by_id)
    components: list[list[SecurityEvent]] = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        component_ids = {start}
        while stack:
            current = stack.pop()
            for neighbor in graph.adjacency.get(current, ()):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component_ids.add(neighbor)
                    stack.append(neighbor)
        components.append([by_id[event_id] for event_id in component_ids])
    return components


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
