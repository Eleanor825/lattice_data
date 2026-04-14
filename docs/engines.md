# Engine Runtime Notes

Lattice now includes an execution layer for compiling normalized JSONL source records through multiple engines:

- `local`
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

The Flink execution path is implemented in code, but `pyflink` is **not installed successfully in the current macOS/arm local environment yet**.

The immediate blocker is the `apache-flink -> apache-beam 2.48.x` dependency chain:

- no matching prebuilt wheel was available for the required Beam version in this environment
- source installation pulled in fragile build steps and failed during dependency compilation

So the current state is:

- the repository is **Flink-compatible at the code level**
- the local environment is **not yet fully Flink-ready**

## Why This Still Matters

This is not just a documentation distinction.

The codebase now has:

- a shared engine abstraction
- local execution
- Spark execution
- a Flink execution entrypoint and runtime checks

That means the platform is no longer purely conceptual. It already runs locally and through Spark, and it has a concrete place to attach a working Flink runtime as soon as the environment dependency issue is resolved.

## Recommended Next Step for Full Flink Runtime

To get Flink fully running, the safest next step is to prepare one of these environments:

1. a clean Python environment that matches a known-good PyFlink + Beam toolchain
2. a containerized local runtime for Flink
3. a binary/distribution-based Flink setup instead of relying on the current pip dependency chain

