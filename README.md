# Lattice

Lattice is an open-source domain data compiler for turning heterogeneous scientific sources into training-ready dataset views.

## Goal

The immediate goal of Lattice is to build **Phase 1** of a materials/scientific data compiler:

- connect heterogeneous real-world scientific sources
- normalize them into a small stable schema family
- preserve provenance, licensing, and dedup metadata
- compile them into reusable dataset views for model training

The longer-term goal is to turn this into a full data-centric research platform:

- Phase 1: data ingestion, normalization, compilation, and release
- Phase 2: data valuation, mixture selection, and feeding strategy optimization

The current implementation targets **Phase 1** of the research plan:

- ingest text, HTML, JSON, JSONL, and optional PDF sources
- normalize them into a minimal schema family
- attach provenance and dedup metadata
- filter low-value inputs
- export multiple dataset views for training and evaluation

It now also includes a **real-source demo fetcher** that can pull a small public sample from:

- OpenAlex
- arXiv
- PubChem
- OQMD
- NOMAD
- Materials Project (when `MP_API_KEY` is set)

## Project Layout

- `src/lattice/`: Python package
- `configs/`: source registry and fetch configuration
- `docs/`: project docs, storage notes, and research notes
- `docs/research/`: proposal, source survey, and planning documents
- `examples/materials/raw/`: sample materials/science inputs
- `tests/`: unit and end-to-end tests

## Repository Status

The repository is currently organized around a compact but runnable Phase 1 baseline:

- source fetchers for public demo sources and selected P0 materials sources
- a schema boundary for normalized records
- compilation into pretraining, QA, instruction, and knowledge views
- reports for manifest, source coverage, and dataset cards
- tests and CI

## Updates

### 2026-04-13

- Initialized the repository as an independent open-source project.
- Implemented the first runnable Phase 1 compiler:
  - text / HTML / JSON / JSONL / optional PDF ingestion
  - schema normalization
  - provenance and dedup metadata
  - quality filtering
  - dataset view export
- Added the first example materials dataset and end-to-end tests.
- Added open-source scaffolding:
  - MIT license
  - contribution guide
  - changelog
  - CI workflow

### 2026-04-14

- Added a real-source demo fetcher for:
  - OpenAlex
  - arXiv
  - PubChem
- Added a starter source registry and a storage architecture document.
- Added registry-driven P0 materials source adapters for:
  - OQMD
  - NOMAD
  - Materials Project
- Verified that:
  - OQMD and NOMAD can be fetched into raw records
  - those raw records can be compiled into Lattice views
  - Materials Project gracefully skips when no API key is configured

## Minimal Schema Family

- `Document`
- `StructuredRecord`
- `KnowledgeRecord`
- `InstructionTrace`

Each record carries shared metadata:

- `source_id`
- `source_type`
- `url_or_ref`
- `timestamp`
- `license`
- `domain`
- `schema_type`
- `dedup_id`
- `provenance_chain`

## Quickstart

```bash
cd /Users/huanzhang/Desktop/lattice
PYTHONPATH=src python3 -m lattice compile \
  --input examples/materials/raw \
  --output outputs/materials \
  --domain materials \
  --dataset-name Lattice-Materials-v0.1
```

Inspect the generated manifest:

```bash
PYTHONPATH=src python3 -m lattice stats --path outputs/materials
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Or use the convenience targets:

```bash
make compile-example
make test
```

Run a real-source demo:

```bash
PYTHONPATH=src python3 -m lattice demo \
  --raw-output data/demo_raw/solid_state \
  --compiled-output data/demo_compiled/solid_state \
  --domain materials \
  --dataset-name Lattice-Materials-RealDemo \
  --query "solid state battery electrolyte" \
  --compound "lithium iron phosphate" \
  --compound "lithium cobalt oxide"
```

Fetch selected registry-backed sources:

```bash
PYTHONPATH=src python3 -m lattice fetch-sources \
  --output data/p0_materials/li_o \
  --registry configs/source_registry.json \
  --domain materials \
  --source oqmd \
  --source nomad \
  --source materials_project \
  --element Li \
  --element O \
  --limit 2
```

`Materials Project` requires `MP_API_KEY` or `MATERIALS_PROJECT_API_KEY`. If it is missing, the fetcher skips that source and records a warning instead of failing.

## Output Views

The compiler exports four dataset views:

- `pretrain_view.jsonl`
- `qa_view.jsonl`
- `instruction_view.jsonl`
- `knowledge_view.jsonl`

Each item keeps a reference back to the normalized source record and its provenance chain.

## Current Scope

This repository intentionally ships a compact, runnable Phase 1 baseline instead of a broad placeholder framework. The focus is on:

- a stable schema boundary
- reproducible compilation
- provenance tracking
- training-facing dataset views

Future work will add value modeling, proxy experiments, and data mixture optimization.

## Open-Source Status

Phase 1 currently includes:

- runnable compiler CLI
- example materials/science dataset
- dataset manifest, source coverage report, and dataset card generation
- end-to-end tests
- GitHub Actions CI
- contribution and release scaffolding

## Storage Recommendation

For serious use, keep real fetched data **outside the git-tracked repo**.

- use the repo for code, configs, manifests, and small fixtures
- use a separate local data root or object store for raw and compiled datasets

See [docs/storage_architecture.md](docs/storage_architecture.md) for the recommended layout.

## Research Notes

Project-side planning and research documents now live under [docs/research](docs/research/README.md):

- [导师想法总结](docs/research/01_导师想法总结.md)
- [Research Proposal](docs/research/02_research_proposal.md)
- [第二方向与实施路线](docs/research/03_第二方向_实施路线与现有工作对比.md)
- [Phase 1 数据来源调研](docs/research/04_phase1_真实数据来源全景调研.md)
