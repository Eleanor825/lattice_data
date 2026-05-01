# Materials Example

This directory contains a tiny Phase 1 demo corpus for `Lattice-Materials`.

## Sources

- `raw/papers/`: plain-text scientific summaries
- `raw/web/`: HTML source pages
- `raw/structured/`: material property records in JSON

## Expected Behavior

When compiled, the sample corpus should:

- drop one boilerplate file
- deduplicate one repeated paper file
- keep two `Document` records
- keep two `StructuredRecord` records
- export all four dataset views

## Target Compiler Examples

Target spec examples for the phase-1 target compiler live under:

- [`../targets/rag_corpus.yaml`](/Users/huanzhang/lattice/examples/targets/rag_corpus.yaml)
- [`../targets/pretrain_corpus.yaml`](/Users/huanzhang/lattice/examples/targets/pretrain_corpus.yaml)
- [`../targets/sft_dataset.yaml`](/Users/huanzhang/lattice/examples/targets/sft_dataset.yaml)
- [`../targets/preference_dataset.yaml`](/Users/huanzhang/lattice/examples/targets/preference_dataset.yaml)
- [`../targets/eval_dataset.yaml`](/Users/huanzhang/lattice/examples/targets/eval_dataset.yaml)
