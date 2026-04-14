# Lattice

> An open-source data-centric platform for large-model training and optimization in science and materials.

Lattice is a platform for building, organizing, and using high-quality training data across the large-model lifecycle: pretraining, continued pretraining, fine-tuning, and post-training.

It starts from the hardest part first: turning fragmented scientific sources into structured, provenance-aware, training-ready data.

![Lattice roadmap](figures/phase1-phase2-roadmap.png)

## Project Goal

The goal of Lattice is to build a platform that can automatically collect, process, organize, and use high-quality training data from many different sources, and make the full model-training workflow easier to operate.

In the long run, Lattice should support:

- pretraining from scratch
- continued pretraining on top of existing models
- task-specific fine-tuning
- safety and alignment optimization in post-training

And it should let users complete these workflows through:

- conversational interaction
- drag-and-drop composition
- reusable pipeline blocks

The intended experience is that users can assemble large-model training and optimization workflows like building blocks, without needing to hand-write complex code for every step.

## Why This Platform Is Needed

Today, high-quality model training in scientific domains is difficult for two reasons at once:

1. **The data problem**
   Scientific and materials data is fragmented across papers, preprints, databases, repositories, patents, and educational resources.

2. **The workflow problem**
   Even after data is collected, users still need to manually connect data preparation, pretraining, continued pretraining, fine-tuning, and post-training pipelines.

This means that the main bottleneck is not just model design. It is also:

- how to gather data
- how to standardize it
- how to track provenance and licensing
- how to turn it into training-ready views
- how to connect it to downstream training workflows

Lattice is meant to solve both the data layer and the workflow layer, starting from data infrastructure and expanding into training orchestration.

## Platform Structure

Lattice is organized in two phases.

### Phase 1: Data Foundation

Phase 1 builds the data engine of the platform.

Its purpose is to automatically ingest heterogeneous sources and convert them into normalized, provenance-aware, reusable training data.

Phase 1 includes:

- source registry and source adapters
- ingestion from APIs, files, web resources, and databases
- schema normalization
- provenance, licensing, and dedup tracking
- quality filtering and data cleaning
- compiled dataset views for:
  - pretraining
  - QA
  - instruction tuning
  - knowledge records

This is the part of the platform that is currently implemented in the repository.

### Phase 2: Training and Optimization Layer

Phase 2 builds the model-training and optimization layer on top of Phase 1.

Its purpose is to let users move from data preparation to end-to-end model improvement workflows.

Phase 2 is intended to support:

- pretraining
- continued pretraining
- fine-tuning
- post-training for safety and alignment
- data valuation and data selection
- mixture optimization and feeding strategy design
- conversational and low-code workflow control

In short:

- Phase 1 answers: **How do we build high-quality training data?**
- Phase 2 answers: **How do we use that data to train and optimize models more easily and more effectively?**

## Current Status

The repository is currently implementing **Phase 1** of the platform.

What is already in place:

- a runnable compiler CLI
- a stable schema boundary
- provenance-aware normalization
- filtering and deduplication
- compiled dataset views
- a starter source registry
- real-source demo fetchers
- open-source adapters for:
  - OpenAlex
  - Crossref
  - arXiv
  - PubChem
  - OQMD
  - NOMAD
  - JARVIS
  - Wikidata
- Materials Project integration with API-key gating
- engine execution layer for:
  - local
  - Spark
  - Flink-compatible code path
- tests and CI

So today, Lattice is already functioning as the **data foundation layer** of the future platform, but it is not yet the full training platform described above.

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
- Added a local execution layer that can compile normalized records with:
  - local Python execution
  - Spark local mode
  - a Flink-compatible execution path with runtime checks
- Verified local and Spark execution in the current environment.

## Repository Structure

- `src/lattice/`: core package
- `configs/`: source registry and fetch configuration
- `docs/`: architecture notes and research documents
- `docs/research/`: proposal, survey, and planning notes
- `examples/`: small sample inputs
- `tests/`: unit and end-to-end tests

## Roadmap

Near-term priorities:

- expand open-source source coverage in Phase 1
- improve source registry and license gating
- build a stronger silver layer for cross-source alignment
- release a larger materials-domain dataset

Long-term priorities:

- connect Phase 1 outputs to model training workflows
- support pretraining, continued pretraining, fine-tuning, and post-training
- add data valuation and mixture optimization
- add conversational and drag-and-drop workflow control

## Supporting Docs

- [Storage Architecture](docs/storage_architecture.md)
- [Engine Runtime Notes](docs/engines.md)
- [Research Notes Index](docs/research/README.md)
