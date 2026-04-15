from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


RunPhase = Literal["phase1", "phase2"]
RunStatus = Literal["prepared", "running", "completed", "failed"]


@dataclass(slots=True)
class DatasetRef:
    path: str
    compiled: bool
    domain: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class BackendRef:
    backend: str
    model_name: str
    provider: str = "local"
    model_family: str = "open"
    api_base: str = ""
    api_key_env: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ExecutionRef:
    engine: str
    local_only: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowSpec:
    phase: RunPhase
    workflow: str
    run_name: str
    dataset: DatasetRef
    backend: BackendRef
    execution: ExecutionRef
    checkpoint_dir: str = ""
    params: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
