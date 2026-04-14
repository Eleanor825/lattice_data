from __future__ import annotations

import re

from lattice.sources.common import http_get_json, safe_query, timestamp_now
from lattice.utils import normalize_whitespace, slugify


def _strip_jats(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def fetch_crossref_documents(query: str, limit: int, domain: str) -> list[dict[str, object]]:
    url = (
        "https://api.crossref.org/works"
        f"?query={safe_query(query)}&rows={limit}&mailto=h648zhan@uwaterloo.ca"
    )
    payload = http_get_json(url)
    rows: list[dict[str, object]] = []
    for item in payload.get("message", {}).get("items", []):
        titles = item.get("title", [])
        title = normalize_whitespace(titles[0]) if titles else ""
        if not title:
            continue
        abstract = _strip_jats(item.get("abstract", ""))
        doi = item.get("DOI", "")
        publisher = item.get("publisher", "")
        year_parts = item.get("published-print", {}).get("date-parts") or item.get("issued", {}).get("date-parts") or []
        year = ""
        if year_parts and year_parts[0]:
            year = str(year_parts[0][0])
        body_parts = []
        if abstract:
            body_parts.append(abstract)
        if publisher:
            body_parts.append(f"Publisher: {publisher}")
        if year:
            body_parts.append(f"Year: {year}")
        if doi:
            body_parts.append(f"DOI: {doi}")
        if not body_parts:
            body_parts.append(title)
        source_id = f"crossref-{slugify(doi or title)}"
        rows.append(
            {
                "schema_type": "Document",
                "source_type": "crossref",
                "source_id": source_id,
                "url_or_ref": item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
                "timestamp": timestamp_now(),
                "license": "Crossref metadata terms",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "title": title,
                    "text": "\n\n".join(body_parts),
                    "sections": [],
                    "doi": doi,
                    "publisher": publisher,
                    "type": item.get("type", ""),
                },
            }
        )
    return rows

