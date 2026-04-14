from __future__ import annotations

from lattice.sources.common import http_get_json, safe_query, timestamp_now


def fetch_jarvis_structures(elements: list[str], limit: int, domain: str) -> list[dict[str, object]]:
    filter_expr = "elements HAS ALL " + ", ".join(f'"{element}"' for element in elements)
    url = (
        "https://jarvis.nist.gov/optimade/jarvisdft/v1/structures/"
        f"?filter={safe_query(filter_expr)}&page_limit={limit}"
    )
    payload = http_get_json(url)
    rows: list[dict[str, object]] = []
    for item in payload.get("data", [])[:limit]:
        attributes = item.get("attributes", {})
        jid = attributes.get("_jarvis_jid") or item.get("id")
        source_id = f"jarvis-{jid}"
        rows.append(
            {
                "schema_type": "StructuredRecord",
                "source_type": "jarvis",
                "source_id": source_id,
                "url_or_ref": f"https://jarvis.nist.gov/jid/{jid}",
                "timestamp": timestamp_now(),
                "license": "JARVIS access terms",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "entity": jid,
                    "entity_type": "material",
                    "fields": {
                        "jid": jid,
                        "elements": ",".join(attributes.get("elements", [])),
                        "formula_anonymous": attributes.get("chemical_formula_anonymous"),
                        "nsites": attributes.get("nsites"),
                        "crystal_system": attributes.get("_jarvis_crys"),
                        "spacegroup": attributes.get("_jarvis_spg"),
                        "formation_energy": attributes.get("_jarvis_form_enp"),
                        "band_gap": attributes.get("_jarvis_gap"),
                        "ehull": attributes.get("_jarvis_ehull"),
                    },
                    "description": f"JARVIS structure {jid} for elements {', '.join(elements)}.",
                },
            }
        )
    return rows

