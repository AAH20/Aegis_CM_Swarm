from __future__ import annotations

from dataclasses import dataclass

from .models import DetectionIntent


@dataclass(frozen=True)
class CompiledDetection:
    backend: str
    query: str
    required_sources: tuple[str, ...]
    semantic_fingerprint: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "query": self.query,
            "required_sources": self.required_sources,
            "semantic_fingerprint": self.semantic_fingerprint,
        }


def compile_detection(intent: DetectionIntent, backend: str) -> CompiledDetection:
    compiler = _COMPILERS.get(backend.lower())
    if compiler is None:
        raise ValueError(f"unsupported backend: {backend}; choose {', '.join(sorted(_COMPILERS))}")
    return CompiledDetection(
        backend=backend.lower(),
        query=compiler(intent),
        required_sources=tuple(sorted({item.source for item in intent.evidence_requirements})),
        semantic_fingerprint=intent.sequence,
    )


def _splunk(intent: DetectionIntent) -> str:
    types = ",".join(f'"{value}"' for value in intent.sequence)
    return (
        f'index=* event_type IN ({types}) | transaction actor maxspan={intent.window_minutes}m '
        f'| where mvcount(event_type)>={len(intent.sequence)} '
        '| table _time actor target event_type source event_id'
    )


def _kql(intent: DetectionIntent) -> str:
    types = ", ".join(f'"{value}"' for value in intent.sequence)
    return (
        f'SecurityEvent | where EventType in ({types}) '
        f'| summarize EventTypes=make_set(EventType), Evidence=make_set(EventId) by Actor, bin(TimeGenerated, {intent.window_minutes}m) '
        f'| where array_length(EventTypes) >= {len(intent.sequence)}'
    )


def _esql(intent: DetectionIntent) -> str:
    types = ", ".join(f'"{value}"' for value in intent.sequence)
    return (
        f'FROM security-* | WHERE event.type IN ({types}) '
        '| STATS behaviors=COUNT_DISTINCT(event.type), evidence=VALUES(event.id) BY user.name '
        f'| WHERE behaviors >= {len(intent.sequence)}'
    )


def _sigma(intent: DetectionIntent) -> str:
    selections = "\n".join(
        f"    selection_{index}:\n      event_type: {event_type}"
        for index, event_type in enumerate(intent.sequence, start=1)
    )
    condition = " and ".join(f"selection_{index}" for index in range(1, len(intent.sequence) + 1))
    return (
        f"title: {intent.name}\nid: {intent.intent_id}\nstatus: experimental\n"
        f"description: {intent.description}\nlogsource:\n  category: security\n"
        f"detection:\n{selections}\n  timeframe: {intent.window_minutes}m\n  condition: {condition}\n"
        f"tags:\n" + "".join(f"  - attack.{technique.lower()}\n" for technique in intent.mitre_techniques)
    )


_COMPILERS = {"splunk": _splunk, "kql": _kql, "esql": _esql, "sigma": _sigma}
