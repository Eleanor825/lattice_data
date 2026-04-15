from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from lattice.compiler import CompilerConfig, compile_dataset
from lattice.platform.runtime import build_phase1_spec
from lattice.platform.sync import sync_phase1_manifest
from lattice.silver import SilverLinkConfig, build_silver_layer
from lattice.sources.common import timestamp_now
from lattice.sources.fetchers import SourceFetchConfig, implemented_sources, run_source_fetch
from lattice.utils import ensure_dir, slugify, write_json


@dataclass(slots=True)
class Phase1Config:
    data_root: str
    registry_path: str
    domain: str
    release_name: str
    query: str = "solid state battery electrolyte"
    elements: list[str] = field(default_factory=lambda: ["Li", "O"])
    compounds: list[str] = field(default_factory=lambda: ["lithium iron phosphate", "lithium cobalt oxide"])
    sources: list[str] = field(default_factory=list)
    limit: int = 3
    include_optional_sources: bool = False
    registry_db: str = ""


def _release_paths(config: Phase1Config) -> dict[str, Path]:
    release_id = slugify(config.release_name)
    root = Path(config.data_root).expanduser()
    date_str = timestamp_now()[:10]
    return {
        "root": root,
        "raw": root / "raw" / "api" / f"date={date_str}" / f"run={release_id}",
        "bronze": root / "bronze" / f"release={release_id}",
        "silver": root / "silver" / f"release={release_id}",
        "gold": root / "gold" / f"release={release_id}",
        "manifests": root / "manifests" / f"release={release_id}",
    }


def run_phase1_pipeline(config: Phase1Config) -> dict[str, Any]:
    paths = _release_paths(config)
    for path in paths.values():
        ensure_dir(path)
    workflow_spec = build_phase1_spec(config)
    workflow_spec_path = paths["manifests"] / "workflow_spec.json"
    write_json(workflow_spec_path, workflow_spec.to_dict())

    selected_sources = config.sources or implemented_sources(
        config.registry_path, include_optional=config.include_optional_sources
    )

    fetch_manifest = run_source_fetch(
        SourceFetchConfig(
            output_dir=str(paths["raw"]),
            domain=config.domain,
            registry_path=config.registry_path,
            sources=selected_sources,
            query=config.query,
            elements=config.elements,
            compounds=config.compounds,
            limit=config.limit,
        )
    )

    bronze_manifest = compile_dataset(
        CompilerConfig(
            input_dir=str(paths["raw"]),
            output_dir=str(paths["bronze"]),
            domain=config.domain,
            dataset_name=f"{config.release_name}-bronze",
        )
    )

    silver_manifest = build_silver_layer(
        SilverLinkConfig(
            bronze_dir=str(paths["bronze"]),
            output_dir=str(paths["silver"]),
            domain=config.domain,
            release_name=config.release_name,
        )
    )

    gold_manifest = compile_dataset(
        CompilerConfig(
            input_dir=str(paths["raw"]),
            output_dir=str(paths["gold"]),
            domain=config.domain,
            dataset_name=f"{config.release_name}-gold",
        )
    )

    phase1_manifest = {
        "generated_at": timestamp_now(),
        "release_name": config.release_name,
        "domain": config.domain,
        "sources": selected_sources,
        "data_root": str(paths["root"].resolve()),
        "paths": {name: str(path.resolve()) for name, path in paths.items()},
        "config": asdict(config),
        "workflow_spec": workflow_spec.to_dict(),
        "workflow_spec_path": str(workflow_spec_path.resolve()),
        "fetch": fetch_manifest,
        "bronze": bronze_manifest,
        "silver": silver_manifest,
        "gold": gold_manifest,
    }
    write_json(paths["manifests"] / "phase1_manifest.json", phase1_manifest)
    if config.registry_db:
        sync_phase1_manifest(config.registry_db, paths["manifests"] / "phase1_manifest.json")
    return phase1_manifest
