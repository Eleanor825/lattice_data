from __future__ import annotations

from lattice.sources.common import http_get_json, safe_query, timestamp_now
from lattice.utils import slugify


def fetch_wikidata_knowledge(terms: list[str], limit: int, domain: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for term in terms:
        url = (
            "https://www.wikidata.org/w/api.php"
            f"?action=wbsearchentities&search={safe_query(term)}&language=en&format=json&limit={limit}"
        )
        payload = http_get_json(url)
        for item in payload.get("search", []):
            entity_id = item.get("id", "")
            if not entity_id or entity_id in seen_ids:
                continue
            seen_ids.add(entity_id)
            label = item.get("label") or entity_id
            description = item.get("description") or ""
            source_id = f"wikidata-{slugify(entity_id)}"
            rows.append(
                {
                    "schema_type": "KnowledgeRecord",
                    "source_type": "wikidata",
                    "source_id": source_id,
                    "url_or_ref": item.get("concepturi") or f"https://www.wikidata.org/wiki/{entity_id}",
                    "timestamp": timestamp_now(),
                    "license": "CC0",
                    "domain": domain,
                    "provenance_chain": [source_id],
                    "payload": {
                        "subject": label,
                        "predicate": "described_as",
                        "object": description or f"Wikidata entity {entity_id}",
                        "evidence": f"Wikidata entity {entity_id}",
                        "entity_id": entity_id,
                        "matched_term": term,
                    },
                }
            )
    return rows

