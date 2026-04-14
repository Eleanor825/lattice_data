from __future__ import annotations

import json
import os
import sys

from lattice.engines.shared import (
    EngineConfig,
    evaluate_record_dict,
    finalize_processed_rows,
    gather_jsonl_paths,
    write_engine_outputs,
)


def _process_line(line: str) -> dict[str, object]:
    return evaluate_record_dict(json.loads(line))


def run_spark_engine(config: EngineConfig) -> dict[str, object]:
    from pyspark.sql import SparkSession

    python_exec = sys.executable
    os.environ["PYSPARK_PYTHON"] = python_exec
    os.environ["PYSPARK_DRIVER_PYTHON"] = python_exec
    spark = (
        SparkSession.builder.master("local[*]")
        .appName("lattice-engine")
        .config("spark.ui.enabled", "false")
        .config("spark.pyspark.python", python_exec)
        .config("spark.pyspark.driver.python", python_exec)
        .getOrCreate()
    )
    try:
        sc = spark.sparkContext
        paths = gather_jsonl_paths(config.input_dir)
        if not paths:
            return write_engine_outputs(
                config=config,
                raw_record_count=0,
                kept_records=[],
                dropped={},
                source_counts={},
                warnings=["No JSONL inputs found for Spark engine."],
            )

        base_rdd = None
        for path in paths:
            path_rdd = sc.textFile(str(path))
            base_rdd = path_rdd if base_rdd is None else base_rdd.union(path_rdd)
        assert base_rdd is not None

        processed_rows = base_rdd.map(_process_line).collect()
        kept_records, dropped, source_counts = finalize_processed_rows(processed_rows)
        return write_engine_outputs(
            config=config,
            raw_record_count=len(processed_rows),
            kept_records=kept_records,
            dropped=dropped,
            source_counts=source_counts,
            warnings=[],
        )
    finally:
        spark.stop()


def spark_smoke_check() -> dict[str, object]:
    try:
        from pyspark.sql import SparkSession
    except Exception as exc:
        return {"available": False, "detail": str(exc)}

    try:
        python_exec = sys.executable
        os.environ["PYSPARK_PYTHON"] = python_exec
        os.environ["PYSPARK_DRIVER_PYTHON"] = python_exec
        spark = (
            SparkSession.builder.master("local[*]")
            .appName("lattice-spark-check")
            .config("spark.ui.enabled", "false")
            .config("spark.pyspark.python", python_exec)
            .config("spark.pyspark.driver.python", python_exec)
            .getOrCreate()
        )
        count = spark.sparkContext.parallelize([1, 2, 3]).count()
        return {"available": True, "detail": f"Spark local smoke test passed with count={count}."}
    except Exception as exc:
        return {"available": False, "detail": str(exc)}
    finally:
        try:
            spark.stop()
        except Exception:
            pass
