from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from lattice.sources.arxiv import fetch_arxiv_documents
from lattice.sources.common import ensure_dir, timestamp_now, write_source_jsonl, write_source_manifest
from lattice.sources.crossref import fetch_crossref_documents
from lattice.sources.jarvis import fetch_jarvis_structures
from lattice.sources.materials_project import fetch_materials_project_materials
from lattice.sources.nomad import fetch_nomad_materials
from lattice.sources.openalex import fetch_openalex_documents
from lattice.sources.oqmd import fetch_oqmd_structures
from lattice.sources.patentsview import fetch_patentsview_placeholder
from lattice.sources.pubchem import fetch_pubchem_compounds
from lattice.sources.registry import registry_source_map
from lattice.sources.wikidata import fetch_wikidata_knowledge


SUPPORTED_SOURCES = {
    "openalex",
    "crossref",
    "arxiv",
    "wikidata",
    "jarvis",
    "pubchem",
    "oqmd",
    "nomad",
    "materials_project",
    "patentsview",
}


@dataclass(slots=True)
class SourceFetchConfig:
    output_dir: str
    domain: str
    registry_path: str
    sources: list[str]
    query: str = "solid state battery electrolyte"
    elements: list[str] = field(default_factory=lambda: ["Li", "O"])
    compounds: list[str] = field(
        default_factory=lambda: ["lithium iron phosphate", "lithium cobalt oxide"]
    )
    limit: int = 3


def run_source_fetch(config: SourceFetchConfig) -> dict[str, Any]:
    output_dir = ensure_dir(config.output_dir)
    registry = registry_source_map(config.registry_path)
    warnings: list[str] = []
    counts: dict[str, int] = {}

    for source_name in config.sources:
        if source_name not in registry:
            warnings.append(f"Unknown source in registry: {source_name}")
            continue
        rows: list[dict[str, Any]] = []
        try:
            if source_name == "openalex":
                rows = fetch_openalex_documents(config.query, config.limit, config.domain)
            elif source_name == "crossref":
                rows = fetch_crossref_documents(config.query, config.limit, config.domain)
            elif source_name == "arxiv":
                rows = fetch_arxiv_documents(config.query, config.limit, config.domain)
            elif source_name == "wikidata":
                rows = fetch_wikidata_knowledge(config.compounds or [config.query], config.limit, config.domain)
            elif source_name == "jarvis":
                rows = fetch_jarvis_structures(config.elements, config.limit, config.domain)
            elif source_name == "pubchem":
                rows, source_warnings = fetch_pubchem_compounds(config.compounds, config.domain)
                warnings.extend(source_warnings)
            elif source_name == "oqmd":
                rows = fetch_oqmd_structures(config.elements, config.limit, config.domain)
            elif source_name == "nomad":
                rows = fetch_nomad_materials(config.elements, config.limit, config.domain)
            elif source_name == "materials_project":
                rows, source_warnings = fetch_materials_project_materials(config.elements, config.limit, config.domain)
                warnings.extend(source_warnings)
            elif source_name == "patentsview":
                rows, source_warnings = fetch_patentsview_placeholder()
                warnings.extend(source_warnings)
            else:
                warnings.append(f"Source fetcher not implemented yet: {source_name}")
                continue
        except Exception as exc:
            warnings.append(f"{source_name} fetch failed: {exc}")
            counts[source_name] = 0
            write_source_jsonl(output_dir, source_name, [])
            continue

        write_source_jsonl(output_dir, source_name, rows)
        counts[source_name] = len(rows)

    manifest = {
        "fetched_at": timestamp_now(),
        "domain": config.domain,
        "query": config.query,
        "elements": config.elements,
        "compounds": config.compounds,
        "config": asdict(config),
        "output_dir": str(Path(output_dir).resolve()),
        "counts": counts,
        "warnings": warnings,
    }
    write_source_manifest(output_dir, manifest)
    return manifest


def implemented_sources(registry_path: str | Path, *, include_optional: bool = False) -> list[str]:
    registry = registry_source_map(registry_path)
    names = []
    for name, payload in registry.items():
        if name not in SUPPORTED_SOURCES:
            continue
        priority = str(payload.get("priority", ""))
        if not include_optional and "optional" in priority.lower():
            continue
        names.append(name)
    return names
