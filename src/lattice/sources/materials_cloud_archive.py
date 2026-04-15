from __future__ import annotations

from lattice.sources.common import http_get_json, safe_query, timestamp_now
from lattice.utils import normalize_whitespace, slugify


def fetch_materials_cloud_records(query: str, limit: int, domain: str) -> list[dict[str, object]]:
    url = f"https://archive.materialscloud.org/api/records?q={safe_query(query)}&size={limit}"
    payload = http_get_json(url)
    rows: list[dict[str, object]] = []
    for item in payload.get("hits", {}).get("hits", [])[:limit]:
        metadata = item.get("metadata", {})
        title = normalize_whitespace(metadata.get("title", "")) or normalize_whitespace(item.get("title", ""))
        if not title:
            continue
        description = normalize_whitespace(metadata.get("description", ""))
        source_id = f"materials-cloud-{slugify(item.get('id', title))}"
        rows.append(
            {
                "schema_type": "Document",
                "source_type": "materials_cloud_archive",
                "source_id": source_id,
                "url_or_ref": item.get("links", {}).get("self_html") or item.get("links", {}).get("self") or "",
                "timestamp": timestamp_now(),
                "license": "Materials Cloud record-level terms",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "title": title,
                    "text": description or title,
                    "sections": [],
                    "doi": item.get("links", {}).get("doi") or "",
                    "record_id": item.get("id", ""),
                },
            }
        )
    return rows

