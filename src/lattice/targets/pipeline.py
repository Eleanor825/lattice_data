from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.compiler.quality import filter_records
from lattice.ingest import ingest_directory
from lattice.models import Record
from lattice.sources.common import timestamp_now
from lattice.targets.builders import (
    build_entities,
    build_eval_items,
    build_instruction_samples,
    build_links,
    build_preference_pairs,
    build_pretrain_spans,
    build_rag_chunks,
)
from lattice.targets.planner import build_compilation_plan
from lattice.targets.specs import TargetSpec, load_target_spec
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


def build_target(config: BuildTargetConfig) -> dict[str, Any]:
    spec = load_target_spec(config.target_spec_path)
    plan = build_compilation_plan(spec, selected_sources=config.source_names)

    raw_records, warnings = ingest_directory(config.input_dir, spec.domain)
    kept_records, dropped = filter_records(raw_records)

    output_dir = ensure_dir(config.output_dir)
    outputs_dir = ensure_dir(output_dir / "outputs")
    reports_dir = ensure_dir(output_dir / "reports")

    entities = build_entities(kept_records, spec.domain)
    links = build_links(kept_records, entities)

    output_counts: dict[str, int] = {}
    if spec.target_type == "rag_corpus":
        chunks = build_rag_chunks(kept_records, entities, spec)
        write_jsonl(outputs_dir / "chunks.jsonl", chunks)
        write_jsonl(outputs_dir / "entities.jsonl", entities)
        write_jsonl(outputs_dir / "links.jsonl", links)
        output_counts = {"chunks": len(chunks), "entities": len(entities), "links": len(links)}
    elif spec.target_type == "pretrain_corpus":
        spans = build_pretrain_spans(kept_records, spec)
        write_jsonl(outputs_dir / "pretrain_spans.jsonl", spans)
        output_counts = {"pretrain_spans": len(spans)}
    elif spec.target_type == "sft_dataset":
        samples = build_instruction_samples(kept_records, entities)
        write_jsonl(outputs_dir / "instruction_samples.jsonl", samples)
        output_counts = {"instruction_samples": len(samples)}
    elif spec.target_type == "preference_dataset":
        samples = build_instruction_samples(kept_records, entities)
        pairs = build_preference_pairs(samples)
        write_jsonl(outputs_dir / "preference_pairs.jsonl", pairs)
        output_counts = {"preference_pairs": len(pairs)}
    else:
        items = build_eval_items(kept_records)
        write_jsonl(outputs_dir / "eval_items.jsonl", items)
        output_counts = {"eval_items": len(items)}

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
