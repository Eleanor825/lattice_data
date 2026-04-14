from __future__ import annotations

from lattice.engines.flink import flink_smoke_check, run_flink_engine
from lattice.engines.local import run_local_engine
from lattice.engines.shared import EngineConfig
from lattice.engines.spark import run_spark_engine, spark_smoke_check


def run_engine_compile(config: EngineConfig) -> dict[str, object]:
    if config.engine == "local":
        return run_local_engine(config)
    if config.engine == "spark":
        return run_spark_engine(config)
    if config.engine == "flink":
        return run_flink_engine(config)
    raise ValueError(f"Unsupported engine: {config.engine}")


def engine_check() -> dict[str, object]:
    return {
        "local": {"available": True, "detail": "Local Python engine is always available."},
        "spark": spark_smoke_check(),
        "flink": flink_smoke_check(),
    }

