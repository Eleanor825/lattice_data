from __future__ import annotations

from pathlib import Path

from lattice.ingest.html_adapter import parse_html_file
from lattice.ingest.pdf_adapter import parse_pdf_file
from lattice.ingest.structured_adapter import parse_structured_file
from lattice.ingest.text_adapter import parse_text_file
from lattice.models import Record


def ingest_directory(path: str | Path, domain: str) -> tuple[list[Record], list[str]]:
    root = Path(path)
    records: list[Record] = []
    warnings: list[str] = []
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md"}:
            records.extend(parse_text_file(file_path, domain))
        elif suffix in {".html", ".htm"}:
            records.extend(parse_html_file(file_path, domain))
        elif suffix in {".json", ".jsonl"}:
            records.extend(parse_structured_file(file_path, domain))
        elif suffix == ".pdf":
            parsed = parse_pdf_file(file_path, domain)
            if not parsed:
                warnings.append(f"Skipped PDF without pypdf support: {file_path}")
            records.extend(parsed)
        else:
            warnings.append(f"Unsupported file type: {file_path}")
    return records, warnings

