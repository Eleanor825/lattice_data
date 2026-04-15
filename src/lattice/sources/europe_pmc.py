from __future__ import annotations

from lattice.sources.common import http_get_json, safe_query, timestamp_now
from lattice.utils import normalize_whitespace, slugify


def fetch_europe_pmc_documents(query: str, limit: int, domain: str) -> list[dict[str, object]]:
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={safe_query(query)}&format=json&pageSize={limit}"
    )
    payload = http_get_json(url)
    rows: list[dict[str, object]] = []
    for item in payload.get("resultList", {}).get("result", [])[:limit]:
        title = normalize_whitespace(item.get("title", ""))
        abstract = normalize_whitespace(item.get("abstractText", ""))
        if not title:
            continue
        pmcid = item.get("pmcid", "")
        doi = item.get("doi", "")
        source_id = f"europe-pmc-{slugify(pmcid or doi or title)}"
        body_parts = [part for part in [abstract, f"Journal: {item.get('journalTitle', '')}", f"Year: {item.get('pubYear', '')}", f"DOI: {doi}" if doi else ""] if part]
        rows.append(
            {
                "schema_type": "Document",
                "source_type": "europe_pmc",
                "source_id": source_id,
                "url_or_ref": item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url") or item.get("id", ""),
                "timestamp": timestamp_now(),
                "license": "Europe PMC open access terms",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "title": title,
                    "text": "\n\n".join(body_parts) if body_parts else title,
                    "sections": [],
                    "doi": doi,
                    "pmcid": pmcid,
                },
            }
        )
    return rows

