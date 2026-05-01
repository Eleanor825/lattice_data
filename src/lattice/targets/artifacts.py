from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Artifact:
    artifact_id: str
    artifact_type: str
    domain: str
    payload: dict[str, Any]
    source_refs: list[dict[str, Any]] = field(default_factory=list)
    license_status: str = "unknown"
    quality: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    lineage: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
