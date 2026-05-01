from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.compiler.quality import filter_records
from lattice.ingest import ingest_directory
from lattice.models import Record
from lattice.sources.common import timestamp_now
from lattice.sources.fetchers import SourceFetchConfig, run_source_fetch
from lattice.sources.registry import registry_source_map
from lattice.targets.artifacts import Artifact
from lattice.targets.fusion import build_entity_bundles
from lattice.targets.planner import build_compilation_plan
from lattice.targets.specs import TargetSpec, load_target_spec
from lattice.targets.transforms import build_base_artifacts, register_default_transforms
from lattice.utils import ensure_dir, write_json, write_jsonl


@dataclass(slots=True)
class BuildTargetConfig:
    input_dir: str
    output_dir: str
    target_spec_path: str
    source_names: list[str]
    registry_path: str = "configs/source_registry.json"
    dataset_name: str = ""
    query: str = "solid state battery electrolyte"
    elements: list[str] | None = None
    compounds: list[str] | None = None
    limit: int = 3


def _dataset_name(config: BuildTargetConfig, spec: TargetSpec) -> str:
    if config.dataset_name:
        return config.dataset_name
    return f"{spec.domain}-{spec.target_type}"


def _dataset_card(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Dataset Card: {manifest['dataset_name']}",
        "",
        f"- Target: {manifest['target_type']}",
        f"- Domain: {manifest['domain']}",
        f"- Policy: {manifest['license_policy']}",
        f"- Raw records: {manifest['raw_record_count']}",
        f"- Kept records: {manifest['kept_record_count']}",
        "",
        "## Outputs",
    ]
    for name, count in manifest["output_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Sources"])
    for source_name in manifest["sources"]:
        lines.append(f"- {source_name}")
    lines.extend(["", "## Plan"])
    for transform_name in manifest["plan"]["transforms"]:
        lines.append(f"- {transform_name}")
    return "\n".join(lines) + "\n"


def _source_counts(records: list[Record]) -> dict[str, int]:
    counts: Counter[str] = Counter(record.metadata.source_type for record in records)
    return dict(counts)


def _is_commercial_safe(license_name: str) -> bool:
    lowered = license_name.strip().lower()
    if not lowered or lowered == "unknown":
        return False
    blocked_terms = ("non-commercial", "nc", "all rights reserved")
    return not any(term in lowered for term in blocked_terms)


def _apply_policy(records: list[Record], license_policy: str) -> tuple[list[Record], Counter[str]]:
    kept: list[Record] = []
    dropped: Counter[str] = Counter()
    for record in records:
        license_name = str(record.metadata.license or "unknown")
        if license_policy == "research_only":
            kept.append(record)
            continue
        if license_policy == "exclude_unknown_license" and license_name.strip().lower() == "unknown":
            dropped["policy_unknown_license"] += 1
            continue
        if license_policy == "commercial_safe" and not _is_commercial_safe(license_name):
            dropped["policy_not_commercial_safe"] += 1
            continue
        kept.append(record)
    return kept, dropped


def _source_maturity(priority: str) -> str:
    priority = priority.strip().upper()
    if priority == "P0":
        return "production_candidate"
    if priority == "P1":
        return "experimental"
    return "unknown"


def _build_source_governance(
    source_names: list[str],
    *,
    registry_path: str,
    license_policy: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    registry = registry_source_map(registry_path)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for source_name in source_names:
        payload = registry.get(source_name)
        if payload is None:
            warnings.append(f"Unknown source in governance registry: {source_name}")
            rows.append(
                {
                    "name": source_name,
                    "maturity": "unknown",
                    "license_status": "unknown",
                    "policy_compatible": False,
                }
            )
            continue
        license_status = str(payload.get("license_status", "unknown"))
        compatible = True
        if license_policy == "exclude_unknown_license" and license_status.strip().lower() == "unknown":
            compatible = False
        if license_policy == "commercial_safe" and not _is_commercial_safe(license_status):
            compatible = False
        rows.append(
            {
                "name": source_name,
                "category": str(payload.get("category", "")),
                "priority": str(payload.get("priority", "")),
                "maturity": _source_maturity(str(payload.get("priority", ""))),
                "license_status": license_status,
                "policy_compatible": compatible,
            }
        )
    return rows, warnings


def _artifacts_to_rows(artifacts: list[Artifact]) -> list[dict[str, Any]]:
    return [artifact.payload | _artifact_metadata_payload(artifact) for artifact in artifacts]


def _artifact_metadata_payload(artifact: Artifact) -> dict[str, Any]:
    source_ref = artifact.source_refs[0] if artifact.source_refs else {}
    payload = {
        "license": artifact.license_status,
        "lineage": list(artifact.lineage),
    }
    for key, value in source_ref.items():
        payload[key] = value
    for key, value in artifact.quality.items():
        payload[key] = value
    return payload


def _link_rows(base_artifacts: list[Artifact], entity_artifacts: list[Artifact]) -> list[dict[str, Any]]:
    alias_map: dict[str, str] = {}
    for entity in entity_artifacts:
        for alias in entity.payload.get("aliases", []):
            alias_map[str(alias).strip().lower()] = str(entity.payload["entity_id"])
    rows: list[dict[str, Any]] = []
    for artifact in base_artifacts:
        entity_name = ""
        if artifact.artifact_type == "StructuredRecord":
            entity_name = str(artifact.payload.get("entity", "")).strip()
        elif artifact.artifact_type == "KnowledgeRecord":
            entity_name = str(artifact.payload.get("subject", "")).strip()
        elif artifact.artifact_type == "Document":
            entity_name = str(artifact.payload.get("title", "")).strip()
        if not entity_name:
            continue
        entity_id = alias_map.get(entity_name.lower())
        if not entity_id:
            continue
        source_ref = artifact.source_refs[0] if artifact.source_refs else {}
        rows.append(
            {
                "link_id": f"link-{artifact.artifact_id}-{entity_id}",
                "record_id": artifact.lineage[0] if artifact.lineage else artifact.artifact_id,
                "entity_id": entity_id,
                "source_id": source_ref.get("source_id", ""),
                "source_type": source_ref.get("source_type", ""),
            }
        )
    return rows


def build_target(config: BuildTargetConfig) -> dict[str, Any]:
    spec = load_target_spec(config.target_spec_path)
    plan = build_compilation_plan(spec, selected_sources=config.source_names)
    transforms = register_default_transforms()
    source_governance, governance_warnings = _build_source_governance(
        config.source_names,
        registry_path=config.registry_path,
        license_policy=spec.license_policy,
    )

    raw_records, warnings = ingest_directory(config.input_dir, spec.domain)
    kept_records, dropped = filter_records(raw_records)
    policy_kept_records, policy_dropped = _apply_policy(kept_records, spec.license_policy)
    base_artifacts = build_base_artifacts(policy_kept_records)

    output_dir = ensure_dir(config.output_dir)
    outputs_dir = ensure_dir(output_dir / "outputs")
    reports_dir = ensure_dir(output_dir / "reports")

    entity_artifacts: list[Artifact] = []
    if "record_to_entity" in plan.transforms:
        entity_artifacts = transforms["record_to_entity"].run(base_artifacts, spec)
    entity_bundles = build_entity_bundles(base_artifacts, entity_artifacts)

    output_counts: dict[str, int] = {}
    if spec.target_type == "rag_corpus":
        chunk_artifacts = transforms["document_to_grounded_chunk"].run(base_artifacts + entity_artifacts, spec)
        link_rows = _link_rows(base_artifacts, entity_artifacts)
        write_jsonl(outputs_dir / "chunks.jsonl", _artifacts_to_rows(chunk_artifacts))
        write_jsonl(outputs_dir / "entities.jsonl", _artifacts_to_rows(entity_artifacts))
        write_jsonl(outputs_dir / "links.jsonl", link_rows)
        output_counts = {"chunks": len(chunk_artifacts), "entities": len(entity_artifacts), "links": len(link_rows)}
    elif spec.target_type == "pretrain_corpus":
        span_artifacts = transforms["document_to_pretrain_span"].run(base_artifacts, spec)
        write_jsonl(outputs_dir / "pretrain_spans.jsonl", _artifacts_to_rows(span_artifacts))
        output_counts = {"pretrain_spans": len(span_artifacts)}
    elif spec.target_type == "sft_dataset":
        instruction_artifacts = transforms["record_to_instruction_sample"].run(base_artifacts, spec)
        write_jsonl(outputs_dir / "instruction_samples.jsonl", _artifacts_to_rows(instruction_artifacts))
        output_counts = {"instruction_samples": len(instruction_artifacts)}
    elif spec.target_type == "preference_dataset":
        instruction_artifacts = transforms["record_to_instruction_sample"].run(base_artifacts, spec)
        preference_artifacts = transforms["instruction_sample_to_preference_pair"].run(instruction_artifacts, spec)
        write_jsonl(outputs_dir / "preference_pairs.jsonl", _artifacts_to_rows(preference_artifacts))
        output_counts = {"preference_pairs": len(preference_artifacts)}
    else:
        eval_artifacts = transforms["record_to_eval_item"].run(base_artifacts, spec)
        write_jsonl(outputs_dir / "eval_items.jsonl", _artifacts_to_rows(eval_artifacts))
        output_counts = {"eval_items": len(eval_artifacts)}

    manifest = {
        "generated_at": timestamp_now(),
        "dataset_name": _dataset_name(config, spec),
        "target_type": spec.target_type,
        "domain": spec.domain,
        "license_policy": spec.license_policy,
        "consumer": spec.consumer,
        "input_dir": str(Path(config.input_dir).resolve()),
        "output_dir": str(output_dir.resolve()),
        "config": asdict(config),
        "target_spec": spec.to_dict(),
        "plan": plan.to_dict(),
        "artifact_summary": dict(Counter(artifact.artifact_type for artifact in base_artifacts + entity_artifacts)),
        "entity_bundle_count": len(entity_bundles),
        "entity_conflict_count": sum(len(bundle.conflicts) for bundle in entity_bundles),
        "sources": list(config.source_names),
        "source_governance": source_governance,
        "raw_record_count": len(raw_records),
        "kept_record_count": len(policy_kept_records),
        "dropped_records": dict(dropped + policy_dropped),
        "source_counts": _source_counts(policy_kept_records),
        "output_counts": output_counts,
        "warnings": warnings + governance_warnings,
    }
    write_json(reports_dir / "manifest.json", manifest)
    write_json(reports_dir / "saved_target_spec.json", spec.to_dict())
    write_json(
        reports_dir / "quality_summary.json",
        {
            "target_type": spec.target_type,
            "output_counts": output_counts,
            "dropped_records": dict(dropped + policy_dropped),
            "warnings": warnings,
        },
    )
    (reports_dir / "dataset_card.md").write_text(_dataset_card(manifest), encoding="utf-8")
    return manifest


def build_target_from_sources(config: BuildTargetConfig) -> dict[str, Any]:
    spec = load_target_spec(config.target_spec_path)
    raw_dir = ensure_dir(Path(config.output_dir) / "raw")
    fetch_manifest = run_source_fetch(
        SourceFetchConfig(
            output_dir=str(raw_dir),
            domain=spec.domain,
            registry_path=config.registry_path,
            sources=config.source_names,
            query=config.query,
            elements=config.elements or ["Li", "O"],
            compounds=config.compounds or ["lithium iron phosphate", "lithium cobalt oxide"],
            limit=config.limit,
        )
    )
    manifest = build_target(
        BuildTargetConfig(
            input_dir=str(raw_dir),
            output_dir=config.output_dir,
            target_spec_path=config.target_spec_path,
            source_names=config.source_names,
            registry_path=config.registry_path,
            dataset_name=config.dataset_name,
            query=config.query,
            elements=config.elements,
            compounds=config.compounds,
            limit=config.limit,
        )
    )
    manifest["fetch"] = fetch_manifest
    write_json(Path(config.output_dir) / "reports" / "manifest.json", manifest)
    return manifest
