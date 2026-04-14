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

