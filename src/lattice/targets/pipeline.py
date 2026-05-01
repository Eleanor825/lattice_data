from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.compiler.quality import filter_records
from lattice.ingest import ingest_directory
from lattice.models import Record
from lattice.sources.common import timestamp_now
from lattice.targets.artifacts import Artifact
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
    dataset_name: str = ""


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

    raw_records, warnings = ingest_directory(config.input_dir, spec.domain)
    kept_records, dropped = filter_records(raw_records)
    base_artifacts = build_base_artifacts(kept_records)

    output_dir = ensure_dir(config.output_dir)
    outputs_dir = ensure_dir(output_dir / "outputs")
    reports_dir = ensure_dir(output_dir / "reports")

    entity_artifacts: list[Artifact] = []
    if "record_to_entity" in plan.transforms:
        entity_artifacts = transforms["record_to_entity"].run(base_artifacts, spec)

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
        "sources": list(config.source_names),
        "raw_record_count": len(raw_records),
        "kept_record_count": len(kept_records),
        "dropped_records": dict(dropped),
        "source_counts": _source_counts(kept_records),
        "output_counts": output_counts,
        "warnings": warnings,
    }
    write_json(reports_dir / "manifest.json", manifest)
    (reports_dir / "dataset_card.md").write_text(_dataset_card(manifest), encoding="utf-8")
    return manifest
