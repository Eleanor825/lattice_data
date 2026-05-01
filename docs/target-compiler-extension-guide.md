# Target Compiler Extension Guide

This is the minimal extension path for the current phase-2 target compiler implementation.

## Add a Transform

1. Create a `Transform` with:
   - `name`
   - `input_types`
   - `output_type`
   - `supported_targets`
   - `runner`
2. Register it with `register_transform(...)`.
3. Add a fixture-backed test.

## Example

See:

- [test_transform_extension.py](/Users/huanzhang/lattice/tests/test_transform_extension.py)

This example registers a custom `Document -> DummySummary` transform without changing planner internals.
