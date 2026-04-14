from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from lattice.sources.common import http_get_text, safe_query, timestamp_now
from lattice.utils import normalize_whitespace, slugify


ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def parse_arxiv_feed(xml_text: str, domain: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, Any]] = []
    for entry in root.findall("a:entry", ATOM_NS):
        title = normalize_whitespace(entry.findtext("a:title", default="", namespaces=ATOM_NS))
        summary = normalize_whitespace(entry.findtext("a:summary", default="", namespaces=ATOM_NS))
        if not title or not summary:
            continue
        arxiv_id = entry.findtext("a:id", default="", namespaces=ATOM_NS).strip()
        source_id = f"arxiv-{slugify(arxiv_id.split('/')[-1] or title)}"
        authors = [
            normalize_whitespace(author.findtext("a:name", default="", namespaces=ATOM_NS))
            for author in entry.findall("a:author", ATOM_NS)
        ]
        categories = [category.attrib.get("term", "") for category in entry.findall("a:category", ATOM_NS)]
        body_parts = [summary]
        if authors:
            body_parts.append("Authors: " + ", ".join(author for author in authors if author))
        if categories:
            body_parts.append("Categories: " + ", ".join(category for category in categories if category))
        rows.append(
            {
                "schema_type": "Document",
                "source_type": "arxiv",
                "source_id": source_id,
                "url_or_ref": arxiv_id,
                "timestamp": timestamp_now(),
                "license": "arXiv terms apply",
                "domain": domain,
                "provenance_chain": [source_id],
                "payload": {
                    "title": title,
                    "text": "\n\n".join(body_parts),
                    "sections": [],
                    "authors": authors,
                    "categories": categories,
                },
            }
        )
    return rows


def fetch_arxiv_documents(query: str, limit: int, domain: str) -> list[dict[str, Any]]:
    search_query = f'all:"{query}"'
    url = f"https://export.arxiv.org/api/query?search_query={safe_query(search_query)}&start=0&max_results={limit}"
    xml_text = http_get_text(url)
    return parse_arxiv_feed(xml_text, domain)
