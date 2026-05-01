<div align="right">
  <a href="./README.md">
    <img alt="English" src="https://img.shields.io/badge/English-111827?style=for-the-badge">
  </a>
  <a href="./README.zh-CN.md">
    <img alt="中文" src="https://img.shields.io/badge/中文-2563eb?style=for-the-badge">
  </a>
  <a href="./docs/README.md">
    <img alt="Docs" src="https://img.shields.io/badge/Docs-0f766e?style=for-the-badge">
  </a>
  <a href="./docs/demo.md">
    <img alt="Demo" src="https://img.shields.io/badge/Demo-7c3aed?style=for-the-badge">
  </a>
</div>

# Lattice

Lattice is an open-source target-driven data compiler for science and materials.

It turns fragmented scientific sources into provenance-aware dataset assets for:

- RAG
- pretraining
- supervised fine-tuning
- preference modeling
- evaluation

<p>
  <img src="./figures/lattice-project-architecture.svg" alt="Lattice project architecture" width="100%">
</p>

## What Lattice Does

Lattice provides a single target-compiler workflow for:

1. ingesting heterogeneous scientific sources
2. normalizing them into shared artifacts
3. tracking provenance, licensing, deduplication, and policy state
4. compiling target-specific dataset assets
5. producing reproducible manifests, dataset cards, and workflow summaries
6. connecting compiled assets to platform and training workflows

## Current Scope

| Area | Status | Notes |
|---|---|---|
| Target compiler core path | ✅ Implemented | `TargetSpec`, artifact layer, transform registry, planner, manifests |
| Phase 1 target families | ✅ Implemented | `rag_corpus`, `pretrain_corpus`, `sft_dataset`, `preference_dataset`, `eval_dataset` |
| Open-source science/materials source coverage | ✅ Implemented | OpenAlex, Crossref, arXiv, PubChem, OQMD, NOMAD, JARVIS, Wikidata, Europe PMC, Materials Cloud, and more |
| Target build API and rerun | ✅ Implemented | Platform API submission, registry sync, rerun support |
| Local execution | ✅ Implemented | Local Python and pandas paths |
| Distributed execution | ✅ Implemented | Spark and Flink local runtimes verified |
| Phase 2 training workflows | ✅ Implemented | `pretrain`, `continue`, `finetune`, `posttrain` reference workflows |
| Registry and job API | ✅ Implemented | Run registry, async submission, rerun, manifest sync |
| Workflow-spec execution | ✅ Implemented | Saved specs can be replayed or migrated across engines |
| Conversational / drag-and-drop UI | ◐ In progress | Product direction, not the current repository focus |

## Core Capabilities

| Capability | What it means in this repo |
|---|---|
| Multi-source ingestion | Fetch from APIs, archives, web resources, and structured repositories |
| Stable schema boundary | Convert raw inputs into records and target-compiler artifacts |
| Target-driven compilation | Build dataset assets from `TargetSpec` instead of fixed output views |
| Training-ready and retrieval-ready outputs | Export `rag`, `pretrain`, `sft`, `preference`, and `eval` target assets |
| Provenance and traceability | Preserve source identity, output manifests, registry records, and workflow specs |
| Policy-aware packaging | Apply research-only, commercial-safe, and exclude-unknown policies |
| Engine portability | Run the same data-preparation logic with pandas, Spark, or Flink |
| Training orchestration | Run local reference workflows and provider-backed Phase 2 jobs |
| Reproducibility | Re-execute a saved workflow spec or rerun a registry-backed job |

## Repository Layout

| Path | Purpose |
|---|---|
| `src/lattice/` | Platform source code |
| `configs/` | Source registry and configuration files |
| `examples/` | Demo datasets and runnable examples |
| `docs/` | Structured documentation, comparisons, demos, and research notes |
| `tests/` | End-to-end and component tests |
| `figures/` | README and documentation figures |

## Quick Start

Build a RAG corpus:

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-rag-demo \
  --target-spec examples/targets/rag_corpus.yaml \
  --source openalex \
  --source pubchem
```

Build an SFT dataset:

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-sft-demo \
  --target-spec examples/targets/sft_dataset.yaml
```

Build an eval dataset:

```bash
PYTHONPATH=src python3 -m lattice build-target \
  --input examples/materials/raw \
  --output outputs/target-eval-demo \
  --target-spec examples/targets/eval_dataset.yaml
```

Run the target-compiler benchmark suite:

```bash
make target-bench
```

Legacy and compatibility paths still exist:

- `compile`
- `phase1-run`
- `phase2-run`
- `run-spec`
- `run-rerun`

## Documentation

Detailed material has been moved out of the homepage and into `docs/`.

- [Documentation index](./docs/README.md)
- [Target compiler quickstart](./docs/target-compiler-quickstart.md)
- [Target compiler PRD](./docs/target-compiler-prd.md)
- [Target compiler roadmap](./docs/target-compiler-roadmap.md)
- [Target compiler technical spec](./docs/target-compiler-technical-spec.md)
- [Target compiler validation plan](./docs/target-compiler-validation-plan.md)
- [Target compiler extension guide](./docs/target-compiler-extension-guide.md)
- [Target compiler release checklist](./docs/target-compiler-release-checklist.md)
- [Overview](./docs/overview.md)
- [Phase 1 pipeline](./docs/phase1.md)
- [Training workflows](./docs/training.md)
- [Engine runtime notes](./docs/engines.md)
- [Source catalog](./docs/source-catalog.md)
- [Platform comparison](./docs/platform-comparison.md)
- [Storage architecture](./docs/storage_architecture.md)
- [Demo](./docs/demo.md)
- [Research notes](./docs/research/README.md)
- [Changelog](./CHANGELOG.md)

## Roadmap

- Phase 1: complete the target-compiler product surface and merge-hardening.
- Phase 2: strengthen entity linking, target-aware scoring, source governance, and extension paths.
- Final state: adaptive planning, richer benchmarks, broader governance, and ecosystem growth.

## Status

The repository is runnable today. The target-compiler path has fixture-backed regression coverage for target builds, policy modes, entity linking, scoring, extension, platform API submission, and rerun behavior.
