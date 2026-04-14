# Lattice

> An open-source data compiler for scientific and materials foundation models.

Lattice is a data-centric project for turning fragmented scientific sources into reusable, provenance-aware, training-ready datasets.

![Lattice roadmap](figures/phase1-phase2-roadmap.png)

## Project Goal

The goal of Lattice is to build a long-term data infrastructure for foundation models in science and materials.

We do not want data collection to remain a one-off scraping workflow. We want it to become a reproducible system that can:

- connect heterogeneous scientific sources
- normalize them into a stable schema
- preserve provenance, licensing, and dedup information
- compile them into reusable training-ready dataset views
- eventually learn which data is more valuable and how it should be used

## Why This Project

Scientific and materials data is split across many incompatible sources:

- papers and preprints
- structured materials databases
- chemistry resources
- repositories and archives
- patents
- educational resources

This creates a practical bottleneck:

1. useful data is scattered and hard to unify
2. most collected data is not directly training-ready
3. data usage is still largely heuristic

Lattice exists because progress in scientific foundation models is increasingly constrained by data quality, structure, provenance, and reuse, not just by model architecture.

## What Lattice Builds

### Phase 1: Data Compiler

Phase 1 builds the core data compiler.

Its job is to take heterogeneous raw sources and turn them into normalized, provenance-aware, training-ready records and dataset views.

Phase 1 focuses on:

- source ingestion
- schema normalization
- provenance and license tracking
- deduplication and quality filtering
- compiled outputs for:
  - pretraining
  - QA
  - instruction tuning
  - knowledge records

### Phase 2: Data Intelligence

Phase 2 builds the intelligence layer on top of Phase 1.

Its job is not just to compile data, but to decide which data is more valuable and how it should be used for specific tasks and budgets.

Phase 2 focuses on:

- data valuation
- task-conditioned scoring
- mixture selection
- feeding strategy and curriculum optimization
- proxy experiments for downstream utility estimation

In short:

- Phase 1 asks: **How do we build high-quality scientific training data?**
- Phase 2 asks: **Which data should we use, and how should we use it?**

## Current Status

The repository is currently implementing **Phase 1**.

What is already in place:

- a runnable compiler CLI
- a stable schema boundary
- provenance-aware normalization
- filtering and deduplication
- compiled dataset views
- a starter source registry
- real-source demo fetchers
- P0 materials adapters for:
  - OQMD
  - NOMAD
  - Materials Project with API-key gating
  - OpenAlex
  - Crossref
  - arXiv
  - PubChem
  - Wikidata
  - JARVIS
- tests and CI

## Repository Structure

- `src/lattice/`: core package
- `configs/`: source registry and fetch configuration
- `docs/`: architecture notes and research documents
- `docs/research/`: proposal, survey, and planning notes
- `examples/`: small sample inputs
- `tests/`: unit and end-to-end tests

## Daily Updates

### 2026-04-13

- Created the standalone `lattice` repository and pushed the first public version.
- Implemented the first runnable Phase 1 compiler:
  - text / HTML / JSON / JSONL / optional PDF ingestion
  - schema normalization
  - provenance and dedup metadata
  - quality filtering
  - compiled dataset views
- Added the first materials example dataset and end-to-end tests.
- Added open-source scaffolding:
  - MIT license
  - contributing guide
  - changelog
  - CI workflow

### 2026-04-14

- Added a real-source demo fetcher for OpenAlex, arXiv, and PubChem.
- Added a starter source registry and storage architecture document.
- Added registry-driven P0 materials source adapters for OQMD, NOMAD, and Materials Project.
- Verified:
  - OQMD and NOMAD can be fetched into raw records
  - fetched records can be compiled into Lattice views
  - Materials Project skips safely when no API key is configured
- Reorganized the repository structure and moved planning documents into `docs/research/`.
- Added the Phase 1 / Phase 2 roadmap figure.

### 2026-04-15

- Extended open-source source coverage with:
  - Crossref
  - Wikidata
  - JARVIS
- Extended the compiler so `KnowledgeRecord` sources can also flow into QA, instruction, and knowledge views.
- Marked PatentsView as an optional connector while the legacy API remains discontinued during ODP migration.

## Roadmap

Near-term priorities:

- expand Phase 1 source coverage
- improve source registry and license gating
- build a stronger silver layer for cross-source alignment
- release a larger materials-domain dataset

Long-term priorities:

- add value modeling
- add mixture optimization
- add feeding strategy optimization

## Supporting Docs

- [Storage Architecture](docs/storage_architecture.md)
- [Research Notes Index](docs/research/README.md)
