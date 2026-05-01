# Lattice Target Compiler Validation Plan

Status: Draft v0.1  
Owner: Product / Research Engineering  
Audience: engineering, research, maintainers, reviewers  
Last Updated: 2026-04-30

## 1. Purpose

This document defines how the target compiler roadmap will be validated.

It covers:

- phase-specific validation goals
- benchmark strategy
- acceptance gates
- release readiness criteria

The staging model is:

- Phase 1 validation
- Phase 2 validation
- Final State validation direction

## 2. Validation Principles

1. Validate workflows, not only code paths.
2. Compare against simple baselines, not only self-consistency.
3. Prefer offline reproducible fixtures for regressions.
4. Use a small number of credible metrics rather than many weak metrics.
5. Require traceability and inspectability as release criteria.

## 3. Phase 1 Validation Plan

## 3.1 Phase 1 Validation Objectives

Phase 1 validation objectives:

1. Prove that target-driven compilation is materially different from fixed-view export.
2. Prove that the same source snapshot can support multiple target assets.
3. Prove that RAG, SFT, and eval outputs are good enough to demonstrate product value.
4. Prove that builds are reproducible and inspectable.

## 3.2 Phase 1 Benchmark Set

The phase 1 benchmark set should include:

- a small materials QA set for retrieval evaluation
- a small grounded answerability set for SFT inspection
- a small eval-set rubric audit set
- a duplicate and provenance regression set

These benchmarks do not need to be large. They do need to be:

- inspectable
- stable
- representative

## 3.3 Phase 1 Baselines

Phase 1 should compare against simple baselines:

- naive paper chunking baseline for RAG
- fixed-view export baseline for SFT
- hand-assembled minimal eval items baseline for eval

The goal is not to beat frontier systems. The goal is to show that target-driven compilation is useful.

## 3.4 Phase 1 Metrics

### RAG Metrics

- citation completeness rate
- duplicate chunk rate
- retrieval hit quality on benchmark queries
- entity coverage in retrieved chunks

### SFT Metrics

- answerability rate
- evidence completeness rate
- provenance completeness rate
- task mixture sanity

### Eval Metrics

- rubric completeness rate
- judgeability rate
- grounded evidence coverage
- conflict-case presence

### System Metrics

- successful rebuild rate from saved manifests
- fixture-only regression pass rate
- source exclusion explainability

## 3.5 Phase 1 Release Gates

Phase 1 should not release publicly as a target compiler unless all gates below are met.

### Gate A: Structural Readiness

- target builds run through `TargetSpec`
- manifests include plan and lineage
- outputs are target-specific, not just fixed-view aliases

### Gate B: Workflow Readiness

- one RAG workflow is demo-ready
- one SFT workflow is demo-ready
- one eval workflow is demo-ready

### Gate C: Reproducibility Readiness

- default demos run with offline fixtures
- rebuild from saved spec succeeds
- source and artifact drops are inspectable

### Gate D: Trust Readiness

- citation payloads are present for RAG outputs
- provenance is preserved in SFT and eval outputs
- policy mode behavior is at least minimally visible

## 3.6 Phase 1 Deliverable Validation

Deliverables that must be validated:

- `rag_corpus` example
- `sft_dataset` example
- `eval_dataset` example
- `pretrain_corpus` example
- `preference_dataset` example
- target spec example library
- benchmark summary document

## 4. Phase 2 Validation Plan

## 4.1 Phase 2 Validation Objectives

Phase 2 validation objectives:

1. Show measurable quality improvement over phase 1.
2. Show that policy-aware and target-aware behavior is real, not nominal.
3. Show that entity-centric compilation improves trust and reuse.
4. Show that extension points are practical for outside contributors.

## 4.2 Phase 2 Benchmark Expansion

Phase 2 should expand validation to include:

- stronger cross-source entity tests
- harder retrieval benchmarks
- more conflict-rich property cases
- policy-mode comparison cases
- source extension integration tests

## 4.3 Phase 2 Metrics

### Linking and Fusion Metrics

- entity linking precision
- entity linking coverage
- conflict visibility rate
- property traceability rate

### Target Quality Metrics

- RAG benchmark gain over phase 1
- SFT evidence completeness gain over phase 1
- eval judgeability gain over phase 1
- preference pair validity gain over phase 1

### Extensibility Metrics

- time to add a new transform
- time to add a new supported source with fixtures
- regression isolation quality

## 4.4 Phase 2 Release Gates

### Gate A: Quality Improvement

- target quality benchmarks show material gains over phase 1

### Gate B: Policy Improvement

- policy presets produce explainable output differences

### Gate C: Ecosystem Improvement

- at least one extension path is documented and practical

### Gate D: Trust Improvement

- conflict and evidence behavior is clearer and more inspectable than in phase 1

## 5. Final State Validation Direction

The final state will require validation beyond fixed benchmark snapshots.

Likely areas:

- feedback-loop effectiveness
- long-term reproducibility
- dataset version drift analysis
- downstream model impact from compiled target quality
- community extension adoption

This is not a phase-one blocker and should remain out of the first implementation critical path.

## 6. Validation Artifacts

Every release stage should maintain:

- benchmark fixture data
- benchmark scripts
- benchmark summary markdown
- release checklist
- known limitations section

## 7. Recommended File Outputs

Suggested validation outputs:

- `benchmarks/README.md`
- `benchmarks/fixtures/`
- `benchmarks/results/phase1-summary.md`
- `benchmarks/results/phase2-summary.md`

The exact directory layout can vary, but the benchmark assets must be versioned in-repo where feasible.

## 8. Release Checklist by Stage

## 8.1 Phase 1 Release Checklist

- target spec build path works
- target-specific manifests exist
- RAG benchmark comparison exists
- SFT example set exists
- eval example set exists
- fixture-only regression suite exists
- docs and quickstarts exist

## 8.2 Phase 2 Release Checklist

- policy modes validated
- linking quality benchmark improved
- source extension guide validated
- target quality summaries updated

## 8.3 Final State Checklist Direction

- feedback loops validated
- ecosystem extensions validated
- stronger adoption and reproducibility evidence collected

## 9. Known Validation Risks

1. Benchmarks become too narrow and overfit to the demo.
2. Quality claims are made without clear baselines.
3. Live APIs creep back into default validation.
4. Preference validation remains too weak to be trusted.
5. Entity-linking metrics are hard to define without a curated benchmark slice.

## 10. Recommendations

- Keep phase 1 validation small but honest.
- Prefer direct baseline comparisons over complicated internal metrics.
- Make inspection and traceability part of the release gate.
- Use phase 2 to improve sophistication, not to excuse weak phase 1 evidence.
