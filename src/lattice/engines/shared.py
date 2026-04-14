from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.compiler.pipeline import _dataset_card, _schema_counts, _source_counts
from lattice.compiler.quality import compute_quality
from lattice.compiler.transforms import build_views
from lattice.models import Record, record_from_dict
from lattice.utils import ensure_dir, write_json, write_jsonl


IGNORED_FILENAMES = {"fetch_manifest.json", "manifest.json", "source_coverage.json"}


@dataclass(slots=True)
class EngineConfig:
    input_dir: str
    output_dir: str
    domain: str
    dataset_name: str
    engine: str
    chunk_size: int = 1200


def gather_jsonl_paths(input_dir: str | Path) -> list[Path]:
    root = Path(input_dir)
    paths = [
        path
        for path in sorted(root.rglob("*.jsonl"))
        if path.is_file() and path.name not in IGNORED_FILENAMES
    ]
    return paths


def load_record_dicts_from_jsonl(input_dir: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in gather_jsonl_paths(input_dir):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def evaluate_record_dict(record_dict: dict[str, Any]) -> dict[str, Any]:
    record = record_from_dict(record_dict)
    quality = compute_quality(record)
    record.quality = quality
    drop_reason = None
    if record.schema_type in {"Document", "InstructionTrace"} and quality["word_count"] < 12:
        drop_reason = "too_short"
    elif quality["has_boilerplate"]:
        drop_reason = "boilerplate"
    elif record.schema_type == "Document" and float(quality["unique_ratio"]) < 0.30:
        drop_reason = "low_information_density"
    return {
        "record": record.to_dict(),
        "keep": drop_reason is None,
        "drop_reason": drop_reason,
        "content_hash": str(quality["content_hash"]),
        "source_type": record.metadata.source_type,
    }


def finalize_processed_rows(processed_rows: list[dict[str, Any]]) -> tuple[list[Record], Counter[str], Counter[str]]:
    dropped: Counter[str] = Counter()
    seen_hashes: set[str] = set()
    kept_records: list[Record] = []
    kept_source_counts: Counter[str] = Counter()

    for row in processed_rows:
        reason = row.get("drop_reason")
        if reason:
            dropped[str(reason)] += 1
            continue
        content_hash = str(row["content_hash"])
        if content_hash in seen_hashes:
            dropped["duplicate"] += 1
            continue
        seen_hashes.add(content_hash)
        record = record_from_dict(row["record"])
        record.metadata.dedup_id = content_hash
        record.quality = dict(row["record"].get("quality", {}))
        kept_records.append(record)
        kept_source_counts[record.metadata.source_type] += 1
    return kept_records, dropped, kept_source_counts


def write_engine_outputs(
    *,
    config: EngineConfig,
    raw_record_count: int,
    kept_records: list[Record],
    dropped: Counter[str],
    source_counts: Counter[str],
    warnings: list[str],
) -> dict[str, Any]:
    views = build_views(kept_records, config.dataset_name, config.chunk_size)

    output_dir = ensure_dir(config.output_dir)
    normalized_dir = ensure_dir(output_dir / "normalized")
    views_dir = ensure_dir(output_dir / "views")
    reports_dir = ensure_dir(output_dir / "reports")

    write_jsonl(normalized_dir / "records.jsonl", [record.to_dict() for record in kept_records])
    for view_name, rows in views.items():
        write_jsonl(views_dir / f"{view_name}.jsonl", rows)

    manifest = {
        "dataset_name": config.dataset_name,
        "domain": config.domain,
        "input_dir": str(Path(config.input_dir).resolve()),
        "output_dir": str(output_dir.resolve()),
        "config": asdict(config),
        "engine": config.engine,
        "raw_record_count": raw_record_count,
        "kept_record_count": len(kept_records),
        "dropped_records": dict(dropped),
        "schema_counts": _schema_counts(kept_records),
        "source_counts": dict(source_counts),
        "view_counts": {name: len(rows) for name, rows in views.items()},
        "warnings": warnings,
    }
    write_json(reports_dir / "manifest.json", manifest)
    write_json(reports_dir / "source_coverage.json", manifest["source_counts"])
    (reports_dir / "dataset_card.md").write_text(_dataset_card(manifest), encoding="utf-8")
    return manifest
