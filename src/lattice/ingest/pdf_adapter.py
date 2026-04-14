from __future__ import annotations

from pathlib import Path

from lattice.models import Record, build_metadata
from lattice.utils import normalize_whitespace, stable_hash


def parse_pdf_file(path: str | Path, domain: str) -> list[Record]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    file_path = Path(path)
    reader = PdfReader(str(file_path))
    pages = []
    for page in reader.pages[:3]:
        page_text = page.extract_text() or ""
        if page_text:
            pages.append(page_text)
    text = normalize_whitespace("\n\n".join(pages))
    if not text:
        return []
    title = file_path.stem.replace("_", " ").title()
    metadata = build_metadata(
        source_path=file_path,
        source_type="pdf",
        domain=domain,
        schema_type="Document",
    )
    record_id = f"doc-{stable_hash(metadata.source_id + title)}"
    return [
        Record(
            record_id=record_id,
            schema_type="Document",
            metadata=metadata,
            payload={"title": title, "text": text, "sections": []},
        )
    ]

