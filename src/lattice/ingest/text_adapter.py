from __future__ import annotations

from pathlib import Path

from lattice.models import Record, build_metadata
from lattice.utils import normalize_whitespace, stable_hash


def parse_text_file(path: str | Path, domain: str) -> list[Record]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    text = normalize_whitespace(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    title = file_path.stem.replace("_", " ").title()
    if lines and (lines[0].startswith("# ") or len(lines[0]) < 120):
        title = lines[0].removeprefix("# ").strip()
        body = "\n".join(lines[1:]).strip()
    else:
        body = "\n".join(lines)

    metadata = build_metadata(
        source_path=file_path,
        source_type="text",
        domain=domain,
        schema_type="Document",
    )
    record_id = f"doc-{stable_hash(metadata.source_id + title)}"
    return [
        Record(
            record_id=record_id,
            schema_type="Document",
            metadata=metadata,
            payload={"title": title, "text": body, "sections": []},
        )
    ]

