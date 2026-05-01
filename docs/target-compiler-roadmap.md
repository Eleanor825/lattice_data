# Lattice Target Compiler Roadmap

Status: Draft v0.1  
Owner: Product / Platform  
Audience: Founders, engineering, research, open-source contributors  
Last Updated: 2026-04-30

## 1. Purpose

This roadmap turns the target compiler vision into a staged product plan.

The roadmap is divided into:

- Phase 1: first usable target compiler release
- Phase 2: stronger dataset intelligence and broader product capability
- Final State: the long-term target compiler platform vision

This document should be read together with:

- [Target Compiler PRD](./target-compiler-prd.md)
- [Target Compiler Technical Spec](./target-compiler-technical-spec.md)
- [Target Compiler Validation Plan](./target-compiler-validation-plan.md)

## 2. Product Thesis

Lattice should not evolve into "a bigger source catalog."

Lattice should evolve into a materials-focused target compiler that:

- ingests heterogeneous scientific and materials data
- links that data around meaningful entities and evidence
- compiles target-specific dataset assets
- preserves provenance, policy, and reproducibility

The roadmap therefore optimizes for:

1. target-driven architecture
2. strong initial workflows
3. measurable quality
4. open-source adoption

## 3. Staging Principles

### 3.1 Architecture Before Breadth

The first release must support multiple target families structurally, even if not every target is equally mature.

### 3.2 Strong Workflows Before Full Coverage

The project should first make a few target workflows genuinely useful before expanding source breadth or UI complexity.

### 3.3 Reproducibility Before Scale

The first public release should emphasize deterministic behavior, offline testing, manifests, and lineage over raw source count.

### 3.4 AI4MatSci Fit Before Domain Generalization

The product should become the best data compiler for AI4MatSci before becoming a broader scientific platform.

## 4. Roadmap Summary

## 4.1 Phase 1 Summary

Goal:

Build the first usable materials target compiler with strong support for:

- `rag_corpus`
- `sft_dataset`
- `eval_dataset`

And usable, lower-maturity support for:

- `pretrain_corpus`
- `preference_dataset`

### Phase 1 Product Promise

Given papers and structured materials records, Lattice can compile target-specific dataset assets with provenance, policy metadata, and reproducible manifests.

## 4.2 Phase 2 Summary

Goal:

Turn the first usable target compiler into a trusted and extensible AI4MatSci data platform.

Focus areas:

- stronger entity linking
- better quality scoring
- broader source governance
- target-aware optimization
- stronger API and workflow management

## 4.3 Final State Summary

Goal:

Make Lattice the data compiler layer for AI4MatSci and a plausible general blueprint for scientific data compilation.

Focus areas:

- richer target families
- extensible transform ecosystem
- policy-aware compilation at scale
- feedback loops from training and evaluation back into data compilation

## 5. Phase 1 Roadmap

## 5.1 Phase 1 Objectives

Phase 1 objectives:

1. Introduce `TargetSpec` as a first-class product abstraction.
2. Move from fixed view exports to a target-driven compilation path.
3. Establish a shared artifact layer across targets.
4. Ship three convincing workflows:
   - grounded RAG corpus generation
   - grounded SFT dataset generation
   - grounded evaluation dataset generation
5. Make all default workflows reproducible and testable offline.

## 5.2 Phase 1 Scope

### Included

- materials-only domain scope
- papers plus structured materials data
- shared artifact layer
- transform registry
- rule-based planner
- target-aware manifests
- CLI-based target build flow

### Excluded

- visual low-code interface
- full workflow orchestration service
- learned planning
- RLHF at production quality
- broad multimodal expansion beyond current core data types

## 5.3 Phase 1 Requirements

### Phase 1A: Product Definition Layer

- Define `TargetSpec`
- Define target presets
- Define policy presets
- Define target-level manifests

### Phase 1B: Shared Data Foundation

- Introduce artifact schema family
- Normalize papers and structured records into shared artifacts
- Introduce `Entity` and `EntityBundle`
- Introduce evidence-bearing chunk outputs

### Phase 1C: Planner and Transform System

- Implement transform registry
- Implement rule-based planner
- Implement target-specific build paths
- Record plans in manifests

### Phase 1D: Strong Initial Targets

- strong `rag_corpus`
- strong `sft_dataset`
- strong `eval_dataset`
- workable `pretrain_corpus`
- MVP `preference_dataset`

### Phase 1E: Release Hardening

- offline fixtures
- source maturity metadata
- source governance defaults
- benchmark scripts
- target quickstarts

## 5.4 Phase 1 Deliverables

### Must Deliver

- unified `build-target` CLI
- `TargetSpec` examples for all five target families
- shared artifact schema
- transform registry and planner
- target-level outputs and manifests
- benchmark-backed demos for RAG, SFT, and eval

### Nice to Deliver

- API submission path for target builds
- commercial-safe policy mode
- richer preference generation

## 5.5 Phase 1 Success Criteria

### Functional Success

- a user can compile at least three different target assets from the same source snapshot
- outputs include provenance and manifest data
- build results are reproducible from saved specs

### Quality Success

- RAG outputs outperform a naive paper-chunk baseline
- SFT outputs are evidence-grounded and answerable
- eval outputs are judgeable and include gold evidence

### Adoption Success

- external users can run the examples without live-source dependence
- the project can be demonstrated as more than a fixed-view exporter

## 6. Phase 2 Roadmap

## 6.1 Phase 2 Objectives

Phase 2 objectives:

1. Improve target quality significantly rather than only expanding functionality.
2. Strengthen entity linking, conflict modeling, and artifact reuse.
3. Introduce target-aware optimization and balancing rather than simple rule export.
4. Make the platform easier to extend via plugins and APIs.
5. Build stronger trust through policy controls and evaluation reporting.

## 6.2 Phase 2 Scope

### Included

- stronger entity resolution
- better citation and evidence modeling
- target-aware scoring expansion
- policy-aware source exclusion
- source maturity and licensing matrix
- broader API surface
- stronger benchmark and reporting layer

### Optional

- workflow service improvements
- asynchronous job execution improvements
- packaging for hosted deployment

## 6.3 Phase 2 Requirements

### Phase 2A: Better Data Intelligence

- confidence-aware linking
- conflict-aware property fusion
- conditional property interpretation
- stronger alias and formula normalization

### Phase 2B: Better Target Optimization

- target-aware sampling strategies
- source balancing strategies
- target-specific dedup strategies
- preference pair improvement logic

### Phase 2C: Better Policy and Trust

- stronger license policy presets
- artifact-level policy status
- dataset-level policy reporting
- policy-driven source inclusion and exclusion

### Phase 2D: Better Platform Surfaces

- more stable platform API
- clearer result inspection
- stronger registry integration
- better reproducibility and rerun support

### Phase 2E: Better Open-Source Experience

- plugin development guides
- schema change guidelines
- fixture authoring guides
- example target recipes

## 6.4 Phase 2 Deliverables

### Must Deliver

- measurable entity-linking improvement over phase 1
- target-aware quality score suite
- policy-aware build modes
- expanded benchmark suite
- contributor-ready plugin and source guides

### Nice to Deliver

- improved runtime orchestration
- API-first build and registry experience

## 6.5 Phase 2 Success Criteria

### Functional Success

- more target variants are possible with little or no core compiler surgery
- more sources can be added safely through documented extension points

### Quality Success

- target-specific outputs show meaningful benchmark gains over phase 1
- entity conflict handling is inspectable and trusted

### Ecosystem Success

- external contributors can add sources or transforms
- community-facing examples become credible references

## 7. Final State Roadmap

## 7.1 Final State Vision

The final state is not just a local compiler. It is a domain-grade data compilation layer with:

- reusable artifact standards
- target-driven planning
- policy-aware compilation
- dataset versioning and lineage
- feedback loops from downstream model use

## 7.2 Final State Product Capabilities

### Compilation Intelligence

- richer planner logic
- learned or data-informed target optimization
- source recommendation and quality-aware routing

### Dataset Feedback Loops

- use RAG retrieval failures to improve corpus quality
- use training loss and error slices to identify data gaps
- use eval results to generate new target datasets automatically

### Ecosystem and Platform

- plugin marketplace for transforms and sources
- hosted and local execution options
- stronger dataset browsing and lineage inspection
- richer product interfaces

### Domain Depth

- more materials-specific property reasoning
- more experimental and computational condition modeling
- more support for cross-source disagreement analysis

## 7.3 Final State Success Criteria

- Lattice is recognized as a reusable data infrastructure layer in AI4MatSci
- external contributors build on the target compiler model
- published datasets and demos rely on Lattice manifests and artifact conventions

## 8. Phase-by-Phase Comparison

| Area | Phase 1 | Phase 2 | Final State |
|---|---|---|---|
| Product identity | first usable target compiler | trusted AI4MatSci data platform | ecosystem and infrastructure layer |
| Targets | all five supported structurally, three strong | all five stronger and more configurable | extensible target families |
| Planner | rule-based | richer target-aware optimization | adaptive or learned assistance |
| Linking | practical entity-centric linking | conflict- and confidence-aware linking | deeper domain-grade fusion |
| Policy | basic presets | policy-aware compilation modes | advanced governance and packaging |
| Validation | small benchmark suite | expanded benchmark and reporting | continuous feedback loops |
| Extensibility | internal-first extension model | contributor-ready interfaces | ecosystem-scale plugin model |

## 9. Recommended Execution Strategy

### Immediate Focus

Build phase 1 to the point where one outsider can:

1. read the docs
2. run a target build
3. inspect the outputs
4. understand why Lattice is different from a fixed exporter

### Avoid

- chasing source count
- broad UI work
- prematurely equalizing all targets
- deep runtime complexity before target quality is convincing

### Prioritize

- strong RAG, SFT, and eval stories
- evidence and provenance quality
- testability and reproducibility

## 10. Release Recommendation

The open-source release should first present Lattice as:

> A target-driven data compiler for AI4MatSci.

Not as:

- a generic training platform
- a source crawler collection
- a low-code workflow builder

The roadmap only works if the product message stays aligned with the staged implementation.
