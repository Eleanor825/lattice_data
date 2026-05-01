from __future__ import annotations

from typing import Any

from lattice.sources.common import http_get_json, safe_query, timestamp_now
from lattice.utils import slugify


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    token_positions: dict[int, str] = {}
    for token, positions in inverted_index.items():
        for position in positions:
            token_positions[position] = token
    ordered = [token_positions[index] for index in sorted(token_positions)]
    text = " ".join(ordered)
    return text.replace(" ,", ",").replace(" .", ".").replace(" ;", ";").strip()


def fetch_openalex_documents(query: str, limit: int, domain: str) -> list[dict[str, Any]]:
    url = f"https://api.openalex.org/works?search={safe_query(query)}&per-page={limit}"
    payload = http_get_json(url)
    rows: list[dict[str, Any]] = []
    for work in payload.get("results", []):
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        title = (work.get("title") or "").strip()
        if not title:
            continue
        source_id = f"openalex-{slugify(work.get('id', title).split('/')[-1])}"
        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in work.get("authorships", [])
            if authorship.get("author", {}).get("display_name")
        ]
        body_parts = [
            abstract,
            f"Publication year: {work.get('publication_year', '')}",
            f"Cited by count: {work.get('cited_by_count', 0)}",
        ]
        if authors:
            body_parts.append("Authors: " + ", ".join(authors[:8]))
        doi = work.get("doi") or ""
        if doi:
            body_parts.append(f"DOI: {doi}")
        if not abstract:
            primary_location = work.get("primary_location", {}) or {}
            source = primary_location.get("source", {}) or {}
            venue = source.get("display_name", "")
            if venue:
                body_parts.append(f"Venue: {venue}")
            concepts = [
                concept.get("display_name", "")
                for concept in work.get("concepts", [])
                if concept.get("display_name")
            ]
            if concepts:
                body_parts.append("Concepts: " + ", ".join(concepts[:8]))
        rows.append(
            {
                "schema_type": "Document",
                "source_type": "openalex",
                "source_id": source_id,
                "url_or_ref": work.get("id") or doi or "",
                "timestamp": timestamp_now(),
                "license": "open metadata",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "title": title,
                    "text": "\n\n".join(part for part in body_parts if part),
                    "sections": [],
                    "authors": authors,
                    "doi": doi,
                    "publication_year": work.get("publication_year"),
                },
            }
        )
    return rows
