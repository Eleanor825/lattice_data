# Phase 1 Benchmark Summary

Status: Initial fixture-backed summary

## Covered Workflows

- `rag_corpus`
- `sft_dataset`
- `eval_dataset`
- `pretrain_corpus`
- `preference_dataset`

## What Is Validated

- target builds run from `TargetSpec`
- outputs are target-specific
- manifests and dataset cards are emitted
- provenance fields are preserved
- policy filtering is visible in manifests
- fixture-backed regression tests pass

## Current Benchmark Style

Phase 1 uses small offline fixtures rather than external benchmark services. This keeps the release reproducible and suitable for CI.

## Release Gate Mapping

- Structural readiness: satisfied by target build tests and manifest outputs
- Workflow readiness: satisfied by fixture-backed RAG, SFT, and eval target tests
- Reproducibility readiness: satisfied by rebuild-from-spec test
- Trust readiness: satisfied by citation, provenance, and policy regression tests
