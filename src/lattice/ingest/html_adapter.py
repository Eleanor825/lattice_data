from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from lattice.models import Record, build_metadata
from lattice.utils import normalize_whitespace, stable_hash


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_ignored_tag = False
        self.title = ""
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self.in_title = True
        if tag in {"script", "style"}:
            self.in_ignored_tag = True

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style"}:
            self.in_ignored_tag = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self.in_ignored_tag:
            return
        text = data.strip()
        if not text:
            return
        if self.in_title:
            self.title += text
        else:
            self.parts.append(text)


def parse_html_file(path: str | Path, domain: str) -> list[Record]:
    file_path = Path(path)
    parser = _VisibleTextParser()
    parser.feed(file_path.read_text(encoding="utf-8"))
    body = normalize_whitespace("\n".join(parser.parts))
    title = parser.title or file_path.stem.replace("_", " ").title()
    metadata = build_metadata(
        source_path=file_path,
        source_type="html",
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

