from __future__ import annotations

import json

from lattice.engines.shared import (
    EngineConfig,
    evaluate_record_dict,
    finalize_processed_rows,
    load_record_dicts_from_jsonl,
    write_engine_outputs,
)


def _process_json_line(line: str) -> str:
    row = evaluate_record_dict(json.loads(line))
    return json.dumps(row, ensure_ascii=False)


def run_flink_engine(config: EngineConfig) -> dict[str, object]:
    try:
        from pyflink.common.typeinfo import Types
        from pyflink.datastream import StreamExecutionEnvironment
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Flink engine is not available in this environment. Install apache-flink "
            "and ensure local Java/Flink prerequisites are met."
        ) from exc

    record_dicts = load_record_dicts_from_jsonl(config.input_dir)
    json_lines = [json.dumps(record_dict, ensure_ascii=False) for record_dict in record_dicts]

    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    stream = env.from_collection(json_lines, type_info=Types.STRING())
    processed_stream = stream.map(_process_json_line, output_type=Types.STRING())
    processed_rows = [json.loads(item) for item in processed_stream.execute_and_collect()]
    kept_records, dropped, source_counts = finalize_processed_rows(processed_rows)
    return write_engine_outputs(
        config=config,
        raw_record_count=len(record_dicts),
        kept_records=kept_records,
        dropped=dropped,
        source_counts=source_counts,
        warnings=[],
    )


def flink_smoke_check() -> dict[str, object]:
    try:
        from pyflink.common.typeinfo import Types
        from pyflink.datastream import StreamExecutionEnvironment
    except Exception as exc:
        return {"available": False, "detail": str(exc)}

    try:
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(1)
        stream = env.from_collection(["1", "2", "3"], type_info=Types.STRING())
        count = sum(1 for _ in stream.execute_and_collect())
        return {"available": True, "detail": f"Flink local smoke test passed with count={count}."}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "detail": str(exc)}

