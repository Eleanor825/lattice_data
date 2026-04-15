# Engine Runtime Notes

Lattice now includes an execution layer for compiling normalized JSONL source records through multiple engines:

- `local`
- `pandas`
- `spark`
- `flink`

## What Is Already Verified

### Local engine

Verified in the current environment.

### Spark engine

Verified in local mode with:

- Java available
- `pyspark==3.5.5` installed
- `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` pinned to the active interpreter

The repository now supports:

```bash
PYTHONPATH=src python3 -m lattice engine-check
PYTHONPATH=src python3 -m lattice engine-compile --engine spark ...
```

## Flink Status

The Flink execution path is now runnable in the current local environment.

Validated local prerequisites:

- `apache-flink`
- `apache-flink-libraries`
- Java 17
- Python-side runtime dependencies required by PyFlink

The repository also auto-detects a Homebrew `openjdk@17` installation when available and uses it for local Flink execution.

So the current state is:

- the repository is **Flink-compatible at the code level**
- the local environment is **Flink-runnable** when the runtime stack is present
- Flink remains the least stable engine because its dependency chain is heavier than local Python or Spark

## Why This Still Matters

This is not just a documentation distinction.

The codebase now has:

- a shared engine abstraction
- local execution
- pandas execution
- Spark execution
- a Flink execution entrypoint and runtime checks

That means the platform is no longer purely conceptual. It already runs locally, through Spark, and through a validated local Flink path.

## Migration Rule

If your workflow stays inside the Lattice data contract, migration is fast:

- the input remains normalized JSONL or a compiled Lattice dataset
- the workflow spec does not change
- the model backend does not change
- only the execution engine changes

In that case, moving from `pandas` to `spark` or `flink` does not require business-logic changes. You only switch the `engine` field or rerun from an existing manifest.

Example:

```bash
PYTHONPATH=src python3 -m lattice phase2-migrate \
  --manifest outputs/phase2-demo/phase2_manifest.json \
  --engine spark \
  --output outputs/phase2-demo-spark
```

You can also execute the saved workflow spec directly:

```bash
PYTHONPATH=src python3 -m lattice run-spec \
  --spec outputs/phase2-demo/workflow_spec.json \
  --engine flink \
  --output outputs/phase2-demo-flink
```

And if a registry-backed run needs to be reproduced, you can rerun it from the saved config snapshot:

```bash
PYTHONPATH=src python3 -m lattice run-rerun \
  --db outputs/platform/registry.db \
  --run-id <existing-run-id>
```

## When Changes Are Still Required

You still need code or config updates when one of these changes:

- the raw source format is outside the normalized Lattice schema
- the new runtime has different dependency or cluster settings
- the model backend itself changes, such as moving from local open training to a closed provider connector
- the workload size forces new partitioning, checkpointing, or resource policies

So the short answer is: `pandas -> spark/flink` is designed to be a configuration migration first, not a rewrite.
