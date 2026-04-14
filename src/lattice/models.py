from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lattice.utils import normalize_whitespace, slugify, stable_hash


JsonDict = dict[str, Any]


@dataclass(slots=True)
class Metadata:
    source_id: str
    source_type: str
    url_or_ref: str
    timestamp: str
    license: str
    domain: str
    schema_type: str
    dedup_id: str
    provenance_chain: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)


@dataclass(slots=True)
class Record:
    record_id: str
    schema_type: str
    metadata: Metadata
    payload: JsonDict
    quality: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return {
            "record_id": self.record_id,
            "schema_type": self.schema_type,
            "metadata": self.metadata.to_dict(),
            "payload": self.payload,
            "quality": self.quality,
        }


def metadata_from_dict(payload: JsonDict) -> Metadata:
    return Metadata(
        source_id=str(payload.get("source_id", "")),
        source_type=str(payload.get("source_type", "")),
        url_or_ref=str(payload.get("url_or_ref", "")),
        timestamp=str(payload.get("timestamp", "")),
        license=str(payload.get("license", "unknown")),
        domain=str(payload.get("domain", "")),
        schema_type=str(payload.get("schema_type", "")),
        dedup_id=str(payload.get("dedup_id", "")),
        provenance_chain=list(payload.get("provenance_chain", [])),
    )


def record_from_dict(payload: JsonDict) -> Record:
    metadata_payload = payload.get("metadata", {})
    metadata = metadata_from_dict(metadata_payload)
    return Record(
        record_id=str(payload.get("record_id", "")),
        schema_type=str(payload.get("schema_type", metadata.schema_type)),
        metadata=metadata,
        payload=dict(payload.get("payload", {})),
        quality=dict(payload.get("quality", {})),
    )


def build_metadata(
    *,
    source_path: str | Path,
    source_type: str,
    domain: str,
    schema_type: str,
    url_or_ref: str | None = None,
    timestamp: str = "",
    license_name: str = "unknown",
    source_suffix: str = "",
) -> Metadata:
    path = Path(source_path)
    source_stem = slugify(path.stem)
    source_id = f"{source_stem}{source_suffix}"
    dedup_seed = f"{schema_type}:{source_id}:{path.resolve()}"
    dedup_id = stable_hash(dedup_seed)
    if not timestamp:
        timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return Metadata(
        source_id=source_id,
        source_type=source_type,
        url_or_ref=url_or_ref or str(path),
        timestamp=timestamp,
        license=license_name,
        domain=domain,
        schema_type=schema_type,
        dedup_id=dedup_id,
        provenance_chain=[source_id],
    )


def record_text(record: Record) -> str:
    if record.schema_type == "Document":
        title = record.payload.get("title", "")
        body = record.payload.get("text", "")
        return normalize_whitespace(f"{title}\n\n{body}")
    if record.schema_type == "StructuredRecord":
        entity = record.payload.get("entity", "")
        fields = record.payload.get("fields", {})
        field_parts = [f"{key}: {value}" for key, value in fields.items()]
        return normalize_whitespace(f"{entity}\n" + "\n".join(field_parts))
    if record.schema_type == "KnowledgeRecord":
        return normalize_whitespace(
            f"{record.payload.get('subject', '')} "
            f"{record.payload.get('predicate', '')} "
            f"{record.payload.get('object', '')}"
        )
    if record.schema_type == "InstructionTrace":
        return normalize_whitespace(
            f"{record.payload.get('instruction', '')}\n{record.payload.get('output', '')}"
        )
    return normalize_whitespace(str(record.payload))
