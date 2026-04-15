from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.models import Record, record_from_dict
from lattice.sources.common import timestamp_now
from lattice.utils import ensure_dir, normalize_whitespace, read_json, slugify, stable_hash, write_json, write_jsonl


@dataclass(slots=True)
class SilverLinkConfig:
    bronze_dir: str
    output_dir: str
    domain: str
    release_name: str


def _load_bronze_records(bronze_dir: str | Path) -> list[Record]:
    path = Path(bronze_dir) / "normalized" / "records.jsonl"
    records: list[Record] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(record_from_dict(__import__("json").loads(line)))
    return records


def _normalize_title(value: str) -> str:
    return slugify(normalize_whitespace(value))


def _document_key(record: Record) -> str | None:
    doi = str(record.payload.get("doi", "")).strip().lower()
    if doi:
        return f"doi:{doi}"
    title = str(record.payload.get("title", "")).strip()
    if title:
        return f"title:{_normalize_title(title)}"
    return None


def _entity_key(record: Record) -> str | None:
    if record.schema_type == "StructuredRecord":
        entity = str(record.payload.get("entity", "")).strip()
        if entity:
            return f"entity:{slugify(entity)}"
    if record.schema_type == "KnowledgeRecord":
        subject = str(record.payload.get("subject", "")).strip()
        if subject:
            return f"subject:{slugify(subject)}"
    return None


def build_silver_layer(config: SilverLinkConfig) -> dict[str, Any]:
    records = _load_bronze_records(config.bronze_dir)
    output_dir = ensure_dir(config.output_dir)

    doc_groups: dict[str, list[Record]] = defaultdict(list)
    entity_groups: dict[str, list[Record]] = defaultdict(list)

    for record in records:
        if record.schema_type == "Document":
            key = _document_key(record)
            if key:
                doc_groups[key].append(record)
        if record.schema_type in {"StructuredRecord", "KnowledgeRecord"}:
            key = _entity_key(record)
            if key:
                entity_groups[key].append(record)

    link_clusters: list[dict[str, Any]] = []
    linked_entities: list[dict[str, Any]] = []

    for key, grouped in sorted(doc_groups.items()):
        cluster_id = f"doc-link-{stable_hash(key)}"
        link_clusters.append(
            {
                "cluster_id": cluster_id,
                "cluster_type": "document",
                "link_key": key,
                "domain": config.domain,
                "record_count": len(grouped),
                "record_ids": [record.record_id for record in grouped],
                "source_ids": [record.metadata.source_id for record in grouped],
                "sources": sorted({record.metadata.source_type for record in grouped}),
                "canonical_title": grouped[0].payload.get("title", ""),
            }
        )

    for key, grouped in sorted(entity_groups.items()):
        cluster_id = f"entity-link-{stable_hash(key)}"
        linked_entities.append(
            {
                "cluster_id": cluster_id,
                "cluster_type": "entity",
                "link_key": key,
                "domain": config.domain,
                "record_count": len(grouped),
                "record_ids": [record.record_id for record in grouped],
                "source_ids": [record.metadata.source_id for record in grouped],
                "sources": sorted({record.metadata.source_type for record in grouped}),
                "canonical_name": grouped[0].payload.get("entity") or grouped[0].payload.get("subject", ""),
            }
        )

    write_jsonl(output_dir / "document_links.jsonl", link_clusters)
    write_jsonl(output_dir / "entity_links.jsonl", linked_entities)

    manifest = {
        "generated_at": timestamp_now(),
        "release_name": config.release_name,
        "domain": config.domain,
        "bronze_dir": str(Path(config.bronze_dir).resolve()),
        "output_dir": str(Path(output_dir).resolve()),
        "config": asdict(config),
        "document_clusters": len(link_clusters),
        "entity_clusters": len(linked_entities),
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest
