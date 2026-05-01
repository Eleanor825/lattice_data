# Lattice Target Compiler Technical Specification

Status: Draft v0.2  
Owner: Platform Engineering  
Audience: engineering, research engineering, maintainers  
Last Updated: 2026-05-01

## 1. Purpose

This document turns the target compiler PRD into a staged technical specification.

It defines:

- required schemas
- required interfaces
- required modules
- stage-specific implementation goals
- repository-level mapping

The staging model is:

- Phase 1
- Phase 2
- Final State

## 2. Technical Goals

1. Replace fixed-view compilation with target-driven compilation.
2. Introduce reusable artifact types shared across targets.
3. Introduce a planner that maps `TargetSpec` to execution steps.
4. Make target outputs reproducible, inspectable, and policy-aware.
5. Preserve compatibility where useful without letting compatibility block architecture.

## 3. Current-State Summary

Current repository strengths:

- multi-source ingestion
- normalized record abstraction
- provenance-oriented metadata
- phase1 / phase2 workflow structure
- registry and manifest support

Current repository constraints:

- fixed output views dominate compiler behavior
- shared record abstraction is too shallow for target-level planning
- linking is still mostly string-based
- quality scoring is mostly target-agnostic
- source maturity and policy controls are limited

## 4. Stage Overview

## 4.1 Phase 1 Technical Objective

Ship the first working target compiler architecture with strong support for:

- `rag_corpus`
- `sft_dataset`
- `eval_dataset`

And usable support for:

- `pretrain_corpus`
- `preference_dataset`

Status:

- Completed on the current branch.

## 4.2 Phase 2 Technical Objective

Improve the quality, trustworthiness, and extensibility of the system:

- stronger entity linking
- better scoring
- stronger policy controls
- better extension points

## 4.3 Final State Technical Objective

Reach a robust platform architecture capable of:

- advanced target optimization
- stronger data feedback loops
- broader plugin-based growth

Status:

- In progress on the current branch.

## 5. Required Technical Components

## 5.1 TargetSpec

### Phase 1 Requirements

Define a `TargetSpec` schema with:

- `target_type: str`
- `domain: str`
- `consumer: str`
- `license_policy: str`
- `quality_objectives: list[str]`
- `constraints: dict[str, object]`
- `target_config: dict[str, object]`

### Phase 1 Notes

- YAML and JSON loading are both required.
- The compiler must persist the resolved target spec into the final manifest.

Implemented:

- yes

### Phase 2 Requirements

- schema validation with richer error messages
- preset inheritance
- stricter target-specific validation

### Final State Requirements

- plugin-defined target types
- spec linting
- richer templating and presets

## 5.2 Artifact Schema Family

### Phase 1 Requirements

Replace or extend the current record-centric model with explicit artifact types.

Required shared fields across all artifacts:

- `artifact_id`
- `artifact_type`
- `domain`
- `payload`
- `source_refs`
- `license_status`
- `quality`
- `policy`
- `lineage`

Required artifact types in phase 1:

- `Document`
- `StructuredPropertyRecord`
- `Entity`
- `EntityBundle`
- `EvidenceSpan`
- `GroundedChunk`
- `PretrainSpan`
- `InstructionSample`
- `PreferencePair`
- `EvalItem`

Implemented:

- yes, with first-version `Artifact` and `EntityBundle` support

### Phase 2 Requirements

- confidence fields
- conflict grouping support
- richer condition modeling

### Final State Requirements

- plugin-defined artifact extensions
- richer multimodal artifact references

## 5.3 Transform Registry

### Phase 1 Requirements

Define a transform interface with:

- transform name
- input artifact types
- output artifact type
- supported target types
- deterministic callable
- optional score hook
- optional filter hook

Example conceptual interface:

```python
class Transform:
    name: str
    input_types: tuple[str, ...]
    output_type: str
    supported_targets: set[str]

    def run(self, inputs, context) -> list[Artifact]:
        ...
```

Minimum phase 1 transforms:

- `document_to_grounded_chunk`
- `document_to_pretrain_span`
- `structured_record_to_instruction`
- `entity_bundle_to_instruction`
- `entity_bundle_to_preference_pair`
- `entity_bundle_to_eval_item`
- `conflict_bundle_to_eval_item`

Implemented:

- a first registry-backed transform set exists

### Phase 2 Requirements

- transform-level metrics
- plugin registration path
- target-aware transform variants

### Final State Requirements

- ecosystem-level transform plugins
- richer plan-time transform composition

## 5.4 Planner

### Phase 1 Requirements

Implement a rule-based planner.

Inputs:

- `TargetSpec`
- source registry metadata
- available transform registry

Outputs:

- selected sources
- selected transforms
- scoring profile
- packaging profile
- plan manifest

Planner behavior in phase 1:

- must vary by target type
- must respect policy presets
- must select different packaging for RAG vs pretraining vs SFT

Implemented:

- yes, via a rule-based planner

### Phase 2 Requirements

- more nuanced source selection
- more nuanced balancing and filtering rules
- optional target presets

### Final State Requirements

- planner assist and optimization layers
- richer feedback from historical build quality

## 5.5 Scoring Layer

### Phase 1 Requirements

Keep the base quality layer and add target-aware scores.

Required target-aware scores:

- `retrieval_fitness`
- `pretrain_fitness`
- `sft_fitness`
- `preference_fitness`
- `eval_fitness`

Implemented:

- yes, including breakdown fields for the current target outputs

Phase 1 scoring can be heuristic, but must be target-dependent.

### Phase 2 Requirements

- better weighting
- more domain-sensitive signals
- explicit reporting of scoring contributions

### Final State Requirements

- more adaptive weighting
- feedback-informed score refinement

## 5.6 Policy Layer

### Phase 1 Requirements

Support policy presets:

- `research_only`
- `commercial_safe`
- `exclude_unknown_license`

Required behaviors:

- source filtering by policy
- manifest explanation for exclusions
- artifact-level policy state

Implemented:

- yes, in first-version target build policy filtering and manifest reporting

### Phase 2 Requirements

- stronger source-level policy matrix
- more precise artifact inheritance rules

### Final State Requirements

- richer governance models
- advanced packaging constraints

## 5.7 Packaging Layer

### Phase 1 Requirements

Each target build must emit:

- target dataset files
- `manifest.json`
- `dataset_card.md`
- quality summary
- source coverage summary
- plan summary

Implemented:

- yes

Per target:

- `rag_corpus`: `chunks.jsonl`, `entities.jsonl`, `links.jsonl`
- `pretrain_corpus`: `pretrain_spans.jsonl`
- `sft_dataset`: `instruction_samples.jsonl`
- `preference_dataset`: `preference_pairs.jsonl`
- `eval_dataset`: `eval_items.jsonl`

### Phase 2 Requirements

- richer packaging metadata
- better policy summaries
- stronger benchmark attachments

### Final State Requirements

- richer dataset browsing integration
- platform-level package manifests

## 6. Target-Specific Technical Requirements

## 6.1 `rag_corpus`

### Phase 1

Required output schema fields:

- `chunk_id`
- `text`
- `title`
- `section`
- `source_type`
- `source_ref`
- `entity_ids`
- `citation_payload`
- `license_status`
- `lineage`
- `quality`

Required behavior:

- section-aware chunking
- chunk dedup
- citation preservation
- entity linking

### Phase 2

- better chunk ranking
- hard negative support
- better cross-source evidence grouping

### Final State

- stronger evidence graph output
- query-aware packaging variants

## 6.2 `pretrain_corpus`

### Phase 1

Required behavior:

- broad text extraction
- long-span packing
- boilerplate suppression
- source balancing

### Phase 2

- better redundancy handling
- domain-balanced sampling

### Final State

- richer pretraining curriculum support

## 6.3 `sft_dataset`

### Phase 1

Required behavior:

- grounded task generation
- provenance-preserving instruction samples
- answerability filtering

Task classes to support:

- extraction
- grounded summarization
- grounded QA
- comparison

### Phase 2

- richer task mixture control
- stronger weak supervision

### Final State

- broader post-training data family generation

## 6.4 `preference_dataset`

### Phase 1

Required behavior:

- weakly supervised chosen/rejected generation
- reason-code attachment
- grounding-based preference logic

### Phase 2

- stronger pair construction logic
- clearer conflict-aware pair generation

### Final State

- broader post-training dataset support

## 6.5 `eval_dataset`

### Phase 1

Required behavior:

- grounded QA items
- extraction eval items
- conflict-aware eval items
- evidence and rubric fields

### Phase 2

- better difficulty controls
- better retrieval eval support

### Final State

- broader benchmark family support

## 7. Repository Mapping

## 7.1 Existing Files to Refactor

- [models.py](/Users/huanzhang/lattice/src/lattice/models.py)
- [compiler/pipeline.py](/Users/huanzhang/lattice/src/lattice/compiler/pipeline.py)
- [compiler/transforms.py](/Users/huanzhang/lattice/src/lattice/compiler/transforms.py)
- [compiler/quality.py](/Users/huanzhang/lattice/src/lattice/compiler/quality.py)
- [silver/linking.py](/Users/huanzhang/lattice/src/lattice/silver/linking.py)
- [sources/fetchers.py](/Users/huanzhang/lattice/src/lattice/sources/fetchers.py)
- [workflows/phase1.py](/Users/huanzhang/lattice/src/lattice/workflows/phase1.py)
- [cli.py](/Users/huanzhang/lattice/src/lattice/cli.py)

## 7.2 New Files or Modules to Add

Suggested additions:

- `src/lattice/targets/specs.py`
- `src/lattice/targets/planner.py`
- `src/lattice/targets/registry.py`
- `src/lattice/targets/policies.py`
- `src/lattice/targets/builders/`
- `src/lattice/artifacts.py`

This exact layout can vary, but these responsibilities must exist.

Current implementation note:

- responsibilities now live under `src/lattice/targets/`

## 8. Stage-by-Stage Technical Roadmap

## 8.1 Phase 1 Technical Roadmap

### Work Package 1: TargetSpec and Artifact Foundation

- define `TargetSpec`
- define artifact schema family
- add serialization support

### Work Package 2: Transform Registry and Planner

- define transform interface
- register core transforms
- implement rule-based planner

### Work Package 3: Entity and Evidence Layer

- implement first practical entity linker
- implement evidence-bearing chunk outputs
- implement source-to-entity linking

### Work Package 4: Target Builders

- implement RAG builder
- implement SFT builder
- implement eval builder
- implement basic pretrain and preference builders

### Work Package 5: Product Hardening

- add fixtures
- add manifests
- add docs
- add benchmark scripts

## 8.2 Phase 2 Technical Roadmap

### Work Package 1: Better Linking and Fusion

- confidence and condition modeling
- stronger alias normalization
- conflict bundles

### Work Package 2: Better Scoring

- richer heuristics
- target-aware balancing
- quality reporting improvements

### Work Package 3: Better Governance

- policy matrix
- stricter maturity metadata
- safer defaults

### Work Package 4: Better Extensibility

- plugin-ready registration
- contributor docs
- stable extension points

## 8.3 Final State Technical Roadmap

### Work Package 1: Target Optimization

- richer plan optimization
- more adaptive target selection logic

### Work Package 2: Feedback Loops

- retrieval failure feedback
- training and eval data feedback

### Work Package 3: Ecosystem Architecture

- plugin growth
- package-level lineage browsing
- hosted and local execution patterns

## 9. Compatibility Strategy

### Phase 1

- keep existing fixed-view exports if inexpensive
- do not let existing fixed views define the new architecture

### Phase 2

- deprecate direct fixed-view assumptions where target builders replace them cleanly

### Final State

- fixed views become one compatibility mode, not the system center

## 10. Technical Risks

1. Artifact design becomes overabstract too early.
2. Entity linking quality is too weak for trust.
3. Planner becomes a thin wrapper around hardcoded branches.
4. Preference dataset quality is not convincing enough.
5. Source fixtures lag behind source expansion.

## 11. Technical Recommendations

- Optimize for clean target builder separation.
- Keep phase 1 planner rule-based and inspectable.
- Make manifests and lineage central from day one.
- Keep source defaults conservative.
- Build RAG, SFT, and eval to a high standard before broadening.
