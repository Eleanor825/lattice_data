# Contributing to Lattice

## Scope

Lattice is currently focused on Phase 1 of the project:

- domain data ingestion
- schema normalization
- provenance tracking
- quality filtering
- dataset-view compilation

Contributions that fit this scope are preferred.

## Development

Run the example compiler:

```bash
PYTHONPATH=src python3 -m lattice compile \
  --input examples/materials/raw \
  --output outputs/materials \
  --domain materials \
  --dataset-name Lattice-Materials-v0.1
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Contribution Priorities

High-value contributions:

- new source adapters for scientific/materials data
- better normalization and provenance handling
- stronger dataset-view transforms
- benchmark and evaluation additions
- documentation improvements

Low-priority contributions:

- UI polish without core compiler changes
- agent wrappers that do not improve the compiler itself

## Rules

- Keep the schema boundary stable unless there is a strong reason to change it.
- Every exported record must keep provenance.
- New dataset views should be reproducible from the normalized records.
- Avoid adding heavy dependencies unless they are necessary.

