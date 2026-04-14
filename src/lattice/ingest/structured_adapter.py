from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lattice.models import Record, build_metadata
from lattice.utils import stable_hash


def _scalar_fields(item: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key, value in item.items():
        if isinstance(value, (str, int, float, bool)) and key not in {"entity", "name", "id"}:
            fields[key] = value
    return fields


def _build_structured_record(item: dict[str, Any], file_path: Path, domain: str, index: int) -> Record:
    entity = str(item.get("entity") or item.get("name") or item.get("id") or f"{file_path.stem}-{index}")
    metadata = build_metadata(
        source_path=file_path,
        source_type="structured",
        domain=domain,
        schema_type="StructuredRecord",
        source_suffix=f"-{index}",
    )
    record_id = f"struct-{stable_hash(metadata.source_id + entity)}"
    payload = {
        "entity": entity,
        "entity_type": item.get("entity_type", "material"),
        "fields": _scalar_fields(item),
        "description": item.get("description", ""),
    }
    return Record(
        record_id=record_id,
        schema_type="StructuredRecord",
        metadata=metadata,
        payload=payload,
    )


def parse_structured_file(path: str | Path, domain: str) -> list[Record]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    items: list[dict[str, Any]] = []
    if suffix == ".jsonl":
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    else:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = [payload]
    return [_build_structured_record(item, file_path, domain, idx) for idx, item in enumerate(items, start=1)]

