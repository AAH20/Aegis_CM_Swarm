from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DetectionIntent, SecurityEvent, ValidationError
from .authority import AuthorityTopology


def load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"input does not exist: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {source}: {exc}") from exc


def load_intent(path: str | Path) -> DetectionIntent:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValidationError("intent document must be a JSON object")
    return DetectionIntent.from_dict(value)


def load_events(path: str | Path) -> list[SecurityEvent]:
    value = load_json(path)
    if not isinstance(value, list):
        raise ValidationError("events document must be a JSON array")
    events = [SecurityEvent.from_dict(item) for item in value]
    if len({event.event_id for event in events}) != len(events):
        raise ValidationError("event_id values must be unique")
    return events


def load_authority_topology(path: str | Path) -> AuthorityTopology:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValidationError("authority topology must be a JSON object")
    return AuthorityTopology.from_dict(value)
