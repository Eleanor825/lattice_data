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

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DatasetRef:
        return cls(
            path=str(payload["path"]),
            compiled=bool(payload["compiled"]),
            domain=str(payload["domain"]),
        )


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

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BackendRef:
        return cls(
            backend=str(payload["backend"]),
            model_name=str(payload["model_name"]),
            provider=str(payload.get("provider", "local")),
            model_family=str(payload.get("model_family", "open")),
            api_base=str(payload.get("api_base", "")),
            api_key_env=str(payload.get("api_key_env", "")),
        )


@dataclass(slots=True)
class ExecutionRef:
    engine: str
    local_only: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ExecutionRef:
        return cls(
            engine=str(payload["engine"]),
            local_only=bool(payload.get("local_only", True)),
        )


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

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> WorkflowSpec:
        return cls(
            phase=payload["phase"],  # type: ignore[arg-type]
            workflow=str(payload["workflow"]),
            run_name=str(payload["run_name"]),
            dataset=DatasetRef.from_dict(payload["dataset"]),  # type: ignore[arg-type]
            backend=BackendRef.from_dict(payload["backend"]),  # type: ignore[arg-type]
            execution=ExecutionRef.from_dict(payload["execution"]),  # type: ignore[arg-type]
            checkpoint_dir=str(payload.get("checkpoint_dir", "")),
            params=dict(payload.get("params", {})),  # type: ignore[arg-type]
        )
