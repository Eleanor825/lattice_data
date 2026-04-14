# Runtime Example

This fixture contains normalized JSONL source records for validating the local, Spark, and Flink engine execution paths.

Use it with:

```bash
PYTHONPATH=src python3 -m lattice engine-compile \
  --engine local \
  --input examples/runtime/raw \
  --output outputs/runtime-local \
  --domain materials \
  --dataset-name Lattice-Runtime-Local
```

