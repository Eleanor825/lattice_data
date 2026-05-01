from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from lattice.utils import read_json


SUPPORTED_TARGET_TYPES = {
    "rag_corpus",
    "pretrain_corpus",
    "sft_dataset",
    "preference_dataset",
    "eval_dataset",
}


@dataclass(slots=True)
class TargetSpec:
    target_type: str
    domain: str
    consumer: str = "general"
    license_policy: str = "research_only"
    quality_objectives: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    target_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def target_spec_from_dict(payload: dict[str, Any]) -> TargetSpec:
    target_type = str(payload["target_type"])
    if target_type not in SUPPORTED_TARGET_TYPES:
        raise ValueError(f"Unsupported target_type: {target_type}")
    return TargetSpec(
        target_type=target_type,
        domain=str(payload["domain"]),
        consumer=str(payload.get("consumer", "general")),
        license_policy=str(payload.get("license_policy", "research_only")),
        quality_objectives=[str(item) for item in payload.get("quality_objectives", [])],
        constraints=dict(payload.get("constraints", {})),
        target_config=dict(payload.get("target_config", {})),
    )


def load_target_spec(path: str | Path) -> TargetSpec:
    spec_path = Path(path)
    suffix = spec_path.suffix.lower()
    if suffix == ".json":
        payload = read_json(spec_path)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported target spec format: {spec_path}")
    if not isinstance(payload, dict):
        raise ValueError("Target spec must be a JSON or YAML object.")
    return target_spec_from_dict(payload)
