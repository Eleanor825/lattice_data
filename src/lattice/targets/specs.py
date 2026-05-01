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

SUPPORTED_LICENSE_POLICIES = {
    "research_only",
    "commercial_safe",
    "exclude_unknown_license",
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


def _validate_mapping(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Target spec field '{name}' must be an object.")
    return dict(value)


def _require_str(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Target spec field '{field_name}' is required and must be a non-empty string.")
    return value.strip()


def _validate_target_config(target_type: str, target_config: dict[str, Any]) -> None:
    chunk_targets = {"rag_corpus", "pretrain_corpus"}
    if target_type in chunk_targets and "chunk_size" in target_config:
        chunk_size = target_config["chunk_size"]
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("Target spec field 'target_config.chunk_size' must be a positive integer.")


def target_spec_from_dict(payload: dict[str, Any]) -> TargetSpec:
    target_type = _require_str(payload, "target_type")
    if target_type not in SUPPORTED_TARGET_TYPES:
        raise ValueError(f"Unsupported target_type: {target_type}")
    domain = _require_str(payload, "domain")
    consumer = str(payload.get("consumer", "general")).strip() or "general"
    license_policy = str(payload.get("license_policy", "research_only")).strip() or "research_only"
    if license_policy not in SUPPORTED_LICENSE_POLICIES:
        raise ValueError(f"Unsupported license_policy: {license_policy}")
    quality_objectives = payload.get("quality_objectives", [])
    if not isinstance(quality_objectives, list):
        raise ValueError("Target spec field 'quality_objectives' must be a list.")
    constraints = _validate_mapping("constraints", payload.get("constraints", {}))
    target_config = _validate_mapping("target_config", payload.get("target_config", {}))
    _validate_target_config(target_type, target_config)
    return TargetSpec(
        target_type=target_type,
        domain=domain,
        consumer=consumer,
        license_policy=license_policy,
        quality_objectives=[str(item) for item in quality_objectives],
        constraints=constraints,
        target_config=target_config,
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
