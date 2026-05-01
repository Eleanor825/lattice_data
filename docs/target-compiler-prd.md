# Lattice Target Compiler PRD

Status: Draft v0.3  
Owner: Product / Platform  
Audience: Founders, engineering, research, open-source contributors  
Last Updated: 2026-05-01

## 1. Document Purpose

This PRD defines the first productized version of Lattice as a target-driven data compiler for materials science and AI4MatSci.

The goal is to move Lattice from a source-driven pipeline that exports fixed views into a target-driven platform that compiles heterogeneous materials data into multiple reusable dataset assets:

- RAG corpus
- pretraining corpus
- SFT dataset
- preference dataset
- evaluation dataset

This document is intended to be implementation-oriented. Every major feature area includes concrete functional requirements, scope boundaries, and acceptance criteria.

This PRD is the top-level product document for the target compiler initiative. It is supplemented by:

- [Target Compiler Roadmap](./target-compiler-roadmap.md)
- [Target Compiler Technical Spec](./target-compiler-technical-spec.md)
- [Target Compiler Validation Plan](./target-compiler-validation-plan.md)

This PRD defines the product shape. The roadmap defines stage boundaries. The technical spec defines implementation contracts. The validation plan defines release gates.

Implementation status note:

- Phase 1 is complete on the current target-compiler branch.
- Several Phase 2 foundations are already implemented in a first version.

## 2. Background

Materials and AI4MatSci workflows depend on fragmented, heterogeneous data:

- papers and reviews
- materials databases
- web documentation
- property tables
- knowledge statements
- internally curated notes

Today, most teams still solve this in an ad hoc way:

- fetch a few sources manually
- normalize into local scripts
- build one narrow dataset for one downstream task
- lose provenance, licensing, and reproducibility along the way

Current Lattice already has the foundation of a multi-source ingestion and compilation stack. The limitation is that the current system is still optimized for:

- source ingestion first
- fixed output views second

The next product step is to optimize for:

- target intent first
- dynamic compilation plan second
- dataset asset generation third

## 3. Product Vision

Lattice becomes the data compiler layer for AI4MatSci.

Users declare the target data asset they need, and Lattice automatically decides:

- which sources to use
- how to normalize and link them
- which transforms to apply
- how to filter and rank candidate outputs
- how to package the final dataset with provenance and policy controls

One-sentence product statement:

> Lattice compiles heterogeneous materials data into target-specific, provenance-aware dataset assets for retrieval, training, post-training, and evaluation.

## 4. Product Goals

### 4.1 Primary Goals

1. Support one unified compilation system for five target families:
   - `rag_corpus`
   - `pretrain_corpus`
   - `sft_dataset`
   - `preference_dataset`
   - `eval_dataset`
2. Make provenance, evidence, and licensing first-class outputs rather than optional metadata.
3. Use a shared intermediate artifact layer so different targets reuse the same source foundation.
4. Provide reproducible manifests and workflow specs for every compiled dataset.
5. Make the product usable by materials research labs without requiring custom one-off data engineering.

### 4.2 Secondary Goals

1. Establish an open-source standard data model for AI4MatSci dataset compilation.
2. Enable a plugin ecosystem for source connectors and target transforms.
3. Create a credible product surface for future commercial and hosted offerings.

## 5. Non-Goals

The first productized target compiler release does not aim to:

1. Be a generic multimodal data OS for every scientific domain.
2. Train frontier models end-to-end.
3. Support RLHF pipelines beyond weakly supervised preference pair generation.
4. Solve full ontology alignment across all materials science subdomains.
5. Provide a full visual low-code UI in phase one.

## 6. Target Users

### 6.1 Primary Users

- AI4MatSci researchers building domain datasets
- materials informatics engineers building RAG or fine-tuning pipelines
- platform engineers who need reproducible dataset generation

### 6.2 Secondary Users

- open-source contributors adding new source connectors or transforms
- applied labs building internal materials copilots
- benchmarking teams creating grounded evaluation sets

## 7. Key User Problems

### 7.1 Research User Problems

- "I can access papers and materials DBs, but I cannot quickly turn them into a dataset for my exact downstream task."
- "I do not trust my generated dataset because I cannot trace every item back to source evidence."
- "Every new task forces me to write a new data pipeline."

### 7.2 Engineering User Problems

- "Our ingestion logic is duplicated across RAG, SFT, and eval pipelines."
- "We cannot enforce license policy consistently."
- "We cannot compare dataset versions or reproduce a compilation run cleanly."

## 8. Product Scope

### 8.1 Domain Scope

Phase one focuses only on materials science and AI4MatSci.

### 8.2 Source Scope

Phase one source priority:

- papers: OpenAlex, Europe PMC, arXiv
- structured materials data: PubChem, JARVIS, OQMD, NOMAD, Materials Project where available
- optional documentation sources only after the core sources are stable

Current implementation note:

- The target compiler can now build from pre-existing raw fixtures or fetch selected registry-backed sources first and then compile a target dataset.

### 8.3 Target Scope

Phase one must support the following target families:

- `rag_corpus`
- `pretrain_corpus`
- `sft_dataset`
- `preference_dataset`
- `eval_dataset`

Not all targets need the same completeness in the first cut. The architecture must support all five. Product quality should be strongest first for:

- `rag_corpus`
- `sft_dataset`
- `eval_dataset`

## 9. Core Product Concepts

### 9.1 Source

A fetchable upstream data provider such as OpenAlex or PubChem.

### 9.2 Artifact

A normalized intermediate object produced from one or more sources. Artifacts are reusable across targets.

Planned artifact types:

- `Document`
- `StructuredPropertyRecord`
- `KnowledgeRecord`
- `Entity`
- `EntityBundle`
- `EvidenceSpan`
- `GroundedChunk`
- `PretrainSpan`
- `InstructionSample`
- `PreferencePair`
- `EvalItem`

### 9.3 TargetSpec

A declarative specification of the desired output dataset asset.

Example responsibilities:

- declare target type
- declare domain
- declare consumer or use case
- declare quality objectives
- declare policy constraints
- declare output packaging preferences

### 9.4 Transform

A typed conversion rule that maps one or more artifacts into another artifact.

Examples:

- `Document -> GroundedChunk`
- `Document -> PretrainSpan`
- `StructuredPropertyRecord -> InstructionSample`
- `EntityBundle + EvidenceSpan -> EvalItem`

### 9.5 CompilationPlan

A runtime plan chosen by the compiler after reading the `TargetSpec`.

The plan determines:

- source selection
- artifact generation steps
- linking and fusion stages
- ranking and filtering strategy
- final output packaging

### 9.6 Manifest

A machine-readable and human-readable record of the full compilation run.

## 10. Functional Requirements

## 10.1 FR-A: Target Specification Layer

### Objective

Allow users to specify what dataset they want, not only where data should come from.

### Requirements

- Support a `TargetSpec` object as a first-class input.
- Support loading `TargetSpec` from JSON or YAML.
- Require the following base fields:
  - `target_type`
  - `domain`
  - `consumer`
  - `license_policy`
  - `quality_objectives`
- Support optional constraints:
  - `citation_required`
  - `commercial_safe`
  - `token_budget`
  - `source_allowlist`
  - `source_denylist`
  - `max_items`
  - `min_evidence_confidence`
- Support target-specific sections for:
  - RAG-specific chunking and citation config
  - pretraining-specific packing config
  - SFT task mix config
  - preference pair construction config
  - evaluation rubric config

### Acceptance Criteria

- A user can run compilation from a single `TargetSpec` file.
- The compiler does not require the user to manually choose internal transforms.
- The final manifest stores the original `TargetSpec`.

Current implementation status:

- Implemented.

## 10.2 FR-B: Unified Intermediate Artifact Layer

### Objective

Create a shared data layer used by all targets.

### Requirements

- Extend the current record model into reusable typed artifacts.
- Support separate models for source metadata, artifact payload, quality scores, policy state, and lineage.
- Preserve source-level identifiers and evidence references.
- Support multi-source artifacts such as `EntityBundle`.
- Support artifact serialization to JSONL.

### Acceptance Criteria

- At least five target outputs are generated from shared artifacts rather than from duplicated target-only logic.
- Artifacts can be reloaded from disk without loss of provenance.

Current implementation status:

- Implemented in a first version with a shared `Artifact` type and target-specific outputs.

## 10.3 FR-C: Source Connectors and Ingestion

### Objective

Build a stable, policy-aware ingestion layer for high-value materials sources.

### Requirements

- Mark source connectors by maturity:
  - `production_candidate`
  - `experimental`
  - `placeholder`
- Exclude placeholder connectors from default product workflows.
- Store connector metadata:
  - license expectations
  - rate limits
  - retry policy
  - fixture availability
- Normalize fetched content into source-specific raw snapshots.
- Ensure all default source connectors have offline fixtures for tests.

### Acceptance Criteria

- Default target compilation runs without relying on placeholder connectors.
- CI coverage does not depend on external live APIs for core workflows.

Current implementation status:

- Partially implemented. Source-backed target builds exist, but fixture-backed coverage remains the default trust path.

## 10.4 FR-D: Entity-Centric Linking and Fusion

### Objective

Link papers, database records, and knowledge artifacts around canonical materials entities.

### Requirements

- Canonicalize materials identifiers where possible:
  - chemical formula
  - normalized name
  - aliases
  - optional external IDs
- Link document mentions to structured database entities.
- Build `EntityBundle` artifacts that gather:
  - linked records
  - source list
  - evidence list
  - property candidates
  - conflict markers
- Preserve conflicting values instead of forcing lossy merges.
- Support confidence and condition annotations for structured properties.

### Acceptance Criteria

- A single canonical entity can trace back to multiple linked paper and DB records.
- Property conflicts are visible in output rather than silently discarded.

Current implementation status:

- Partially implemented via entity bundles, evidence aggregation, and conflict counting.

## 10.5 FR-E: Transform Registry

### Objective

Replace hardcoded fixed-output compilation with reusable typed transforms.

### Requirements

- Register transforms by:
  - name
  - input artifact types
  - output artifact type
  - supported targets
  - quality hooks
- Support one-to-one, one-to-many, and many-to-one transforms.
- Support transform-level filtering and scoring hooks.
- Support deterministic execution order within the selected plan.

### Minimum Phase-One Transforms

- `Document -> GroundedChunk`
- `Document -> PretrainSpan`
- `StructuredPropertyRecord -> InstructionSample`
- `EntityBundle -> InstructionSample`
- `EntityBundle -> PreferencePair`
- `EntityBundle -> EvalItem`
- `ConflictBundle -> EvalItem`

### Acceptance Criteria

- Adding a new target-specific transform does not require rewriting the full compiler.
- At least three targets share some transform inputs or intermediate artifacts.

Current implementation status:

- Implemented in a first version with registry-backed transform tests.

## 10.6 FR-F: Compilation Planner

### Objective

Turn a user target into a concrete compilation plan.

### Requirements

- Read `TargetSpec`.
- Select relevant sources.
- Select required transforms.
- Select target-aware scoring functions.
- Select output packaging rules.
- Record plan decisions in the manifest.

### Phase-One Planner Behavior

The phase-one planner can be rule-based rather than learned. It should still behave like a planner, not a fixed exporter.

### Acceptance Criteria

- Different `TargetSpec` values result in different chosen plans.
- The planner output is inspectable in logs and manifests.

Current implementation status:

- Implemented in a rule-based phase-1 form.

## 10.7 FR-G: Target-Aware Quality Scoring

### Objective

Score the same artifact differently depending on downstream use.

### Requirements

- Preserve a shared baseline quality score layer.
- Add target-aware scores:
  - `retrieval_fitness`
  - `pretrain_fitness`
  - `sft_fitness`
  - `preference_fitness`
  - `eval_fitness`
- Allow one artifact to score highly for one target and poorly for another.
- Use target-aware scores in:
  - filtering
  - ranking
  - balancing
  - packaging

### Acceptance Criteria

- At least one artifact set is ranked differently when compiled for RAG versus pretraining.
- Score definitions are stored in code and documented.

Current implementation status:

- Implemented in a first version with per-target score fields and score breakdowns.

## 10.8 FR-H: Policy and License Controls

### Objective

Make data policy a product feature rather than an afterthought.

### Requirements

- Support policy presets:
  - `research_only`
  - `commercial_safe`
  - `exclude_unknown_license`
- Track artifact-level and source-level license status.
- Allow the planner to exclude policy-incompatible sources.
- Include policy summary in output manifest and dataset card.

### Acceptance Criteria

- The same target can be compiled differently under two different policy presets.
- Output manifests clearly explain source exclusions caused by policy rules.

Current implementation status:

- Implemented in a first version for target builds and source governance summaries.

## 10.9 FR-I: Reproducibility and Auditability

### Objective

Every output dataset must be reproducible and inspectable.

### Requirements

- Persist:
  - source manifest
  - target spec
  - compilation plan
  - quality summary
  - output manifest
- Persist artifact lineage.
- Persist source coverage and filtering summary.
- Generate a dataset card for every compiled output.

### Acceptance Criteria

- A user can rerun the exact same target compilation from stored specs.
- A user can inspect why a source or artifact was dropped.

Current implementation status:

- Implemented. Saved target specs, manifests, CLI registry sync, API submission, and rerun are in place.

## 10.10 FR-J: Product Surfaces

### Objective

Provide a usable product entry point for developers and early design partners.

### Requirements

- Add a unified CLI entry point such as:
  - `lattice build-target --target-spec path/to/spec.yaml`
- Add target shortcuts such as:
  - `lattice build-target --target rag_corpus ...`
- Expose target compilation via platform API in a future-compatible way.
- Provide a minimal demo that shows:
  - entity-linked evidence
  - retrieval-ready chunks
  - target-specific manifests

### Acceptance Criteria

- A new user can build a target dataset from a short command plus a small spec file.
- The result directory is understandable without reading internal code.

Current implementation status:

- Implemented for CLI, and partially implemented for platform API.

## 11. Target Definitions

## 11.1 Target: `rag_corpus`

### User Value

Build a retrieval-ready grounded corpus for materials question answering and assistant products.

### Output Requirements

- `chunks.jsonl`
- `entities.jsonl`
- `links.jsonl`
- `manifest.json`
- `dataset_card.md`

### Chunk Requirements

Each chunk must include:

- `chunk_id`
- `text`
- `title`
- `section`
- `source_type`
- `source_ref`
- `entity_ids`
- `license`
- `provenance_chain`
- `citation_payload`
- `retrieval_score`

### Behavior Requirements

- Use section-aware chunking.
- Remove boilerplate.
- Deduplicate near-duplicate chunks.
- Prefer evidence-rich and entity-salient chunks.
- Preserve citation traceability.

### Success Metrics

- retrieval hit quality
- citation completeness
- entity coverage
- duplicate suppression

## 11.2 Target: `pretrain_corpus`

### User Value

Build a broad, relatively clean text corpus for domain pretraining or continued pretraining.

### Output Requirements

- `pretrain_spans.jsonl`
- `manifest.json`
- `dataset_card.md`

### Behavior Requirements

- Allow larger span packing than RAG.
- Down-weight repeated abstracts and boilerplate.
- Allow broader coverage than RAG.
- Support source balancing and span packing rules.

### Success Metrics

- low boilerplate rate
- low duplicate rate
- broad source diversity
- stable span length distribution

## 11.3 Target: `sft_dataset`

### User Value

Build high-quality supervised examples for instruction tuning.

### Output Requirements

- `instruction_samples.jsonl`
- `manifest.json`
- `dataset_card.md`

### Behavior Requirements

- Generate grounded tasks such as:
  - extraction
  - summarization
  - grounded QA
  - comparison
- Require sufficient evidence for answers.
- Preserve provenance in every sample.
- Support task mixture controls.

### Success Metrics

- answerability
- evidence completeness
- task diversity
- low hallucination risk

## 11.4 Target: `preference_dataset`

### User Value

Build weakly supervised chosen/rejected pairs for post-training or answer ranking.

### Output Requirements

- `preference_pairs.jsonl`
- `manifest.json`
- `dataset_card.md`

### Behavior Requirements

- Construct pairs from grounded candidate answers.
- Support weak supervision rules:
  - evidence-supported beats unsupported
  - more complete beats less complete
  - lower conflict beats higher conflict
- Preserve reason codes for every pair.

### Success Metrics

- preference validity
- reason-code clarity
- grounding coverage

## 11.5 Target: `eval_dataset`

### User Value

Build trustworthy evaluation assets for retrieval and model assessment.

### Output Requirements

- `eval_items.jsonl`
- `manifest.json`
- `dataset_card.md`

### Behavior Requirements

- Support grounded QA evaluation.
- Support property extraction evaluation.
- Support cross-source conflict cases.
- Support hard negatives for retrieval evaluation.
- Include gold evidence and rubric fields.

### Success Metrics

- coverage
- difficulty
- rubric completeness
- judgeability

## 12. Detailed Feature Breakdown by Workstream

## 12.1 Workstream: Schema and Model Refactor

### Scope

- extend current record model
- add artifact types
- separate source metadata from target output payloads

### Deliverables

- updated artifact schema definitions
- serialization and deserialization utilities
- schema docs

### Risks

- overdesign before target behavior stabilizes

## 12.2 Workstream: Source Governance

### Scope

- source maturity labels
- source fixture strategy
- policy metadata

### Deliverables

- registry enhancements
- fixture-backed tests
- source support matrix

### Risks

- too many connectors before core workflows are stable

## 12.3 Workstream: Entity Linking

### Scope

- canonicalization
- alias resolution
- document-to-entity linking
- entity bundles

### Deliverables

- entity linker
- linked artifact outputs
- conflict-aware property grouping

### Risks

- entity precision problems will directly damage downstream trust

## 12.4 Workstream: Transform and Planner

### Scope

- transform registry
- target planner
- compilation plan execution

### Deliverables

- transform interface
- planner implementation
- manifest plan export

### Risks

- hardcoded exceptions reappearing inside the planner

## 12.5 Workstream: Target Builders

### Scope

- RAG builder
- pretraining builder
- SFT builder
- preference builder
- eval builder

### Deliverables

- target-specific output packages
- target-specific scoring and filtering
- target docs

### Risks

- trying to make all five targets equally mature in the first release

## 12.6 Workstream: QA, Evaluation, and Benchmarking

### Scope

- offline fixtures
- target-level tests
- benchmark scripts

### Deliverables

- regression suite
- small public benchmark
- quality report template

### Risks

- too much reliance on live API tests

## 13. User Flows

## 13.1 Primary Flow: Build a RAG Corpus

1. User writes a `TargetSpec` for `rag_corpus`.
2. User selects a materials query and source allowlist.
3. Compiler fetches and normalizes data.
4. Compiler links entities and builds evidence-rich chunks.
5. Compiler scores, filters, and deduplicates.
6. Compiler writes final outputs plus manifest and dataset card.

## 13.2 Primary Flow: Build an SFT Dataset

1. User writes a `TargetSpec` for `sft_dataset`.
2. Compiler reuses normalized artifacts and entity bundles.
3. Compiler generates instruction samples.
4. Compiler filters by evidence sufficiency and task mix.
5. Compiler writes packaged SFT outputs and manifest.

## 13.3 Primary Flow: Build an Eval Set

1. User writes a `TargetSpec` for `eval_dataset`.
2. Compiler identifies high-value grounded and conflict-rich artifacts.
3. Compiler generates eval items and attaches rubrics.
4. Compiler writes benchmark-ready eval outputs and manifest.

## 14. Success Metrics

## 14.1 Product Metrics

- number of target builds completed successfully
- number of reusable dataset assets produced per source snapshot
- average reproducibility success rate for reruns

## 14.2 Quality Metrics

- citation completeness rate for RAG outputs
- duplicate suppression rate for chunk outputs
- grounded answer coverage for SFT outputs
- pair validity rate for preference outputs
- benchmark judgeability rate for eval outputs

## 14.3 Community Metrics

- number of external users building datasets from their own specs
- number of contributed connectors or transforms
- number of papers or demos referencing Lattice-generated datasets

## 15. Release Prioritization

## 15.1 P0: Architecture Foundation

Must-have:

- `TargetSpec`
- artifact refactor
- transform registry
- rule-based planner
- manifest integration

## 15.2 P1: Strong Initial Target Support

Must-have:

- strong `rag_corpus`
- strong `sft_dataset`
- strong `eval_dataset`

Good-enough:

- workable `pretrain_corpus`
- MVP `preference_dataset`

## 15.3 P2: Product Hardening

- policy presets
- fixture-backed tests
- improved source reliability
- benchmark reporting
- better API surfaces

## 16. Milestones

### Milestone 1: Spec and Artifact Foundation

- `TargetSpec` schema
- artifact layer refactor
- manifest updates

### Milestone 2: Planner and Transform System

- transform registry
- rule-based planner
- target-specific execution paths

### Milestone 3: First Strong Targets

- RAG corpus
- SFT dataset
- eval dataset

### Milestone 4: Extended Target Family

- pretraining corpus
- preference dataset

### Milestone 5: Open-Source Hardening

- docs
- offline tests
- benchmark examples
- quickstarts

## 17. Open Questions

1. Which materials sources are safe enough to make default for commercial-safe output modes?
2. How strict should the first version of entity canonicalization be?
3. Should `preference_dataset` remain weakly supervised only in phase one?
4. How much of the current fixed-view export path should remain for backward compatibility?
5. Should the first target compiler release expose API submission, or CLI only?

## 18. Recommended Implementation Notes

These are implementation notes rather than product requirements, but they should guide engineering decisions:

- Prefer a shared artifact layer over target-specific shortcuts.
- Preserve current functionality where easy, but do not let old fixed views define the new architecture.
- Treat policy, provenance, and manifests as core product features.
- Optimize for three convincing target workflows before widening source breadth.
- Favor stable offline fixtures for product confidence and open-source adoption.

## 19. Summary

The phase-one product is not "a bigger source catalog."

The phase-one product is a target-driven materials data compiler that:

- ingests heterogeneous materials data
- links and fuses it around meaningful entities
- compiles it into multiple dataset asset types
- preserves evidence, policy, and reproducibility

If implemented well, this becomes a reusable data infrastructure layer for AI4MatSci rather than just another one-off ingestion toolkit.
