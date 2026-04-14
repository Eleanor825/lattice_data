from __future__ import annotations

from lattice.engines.shared import (
    EngineConfig,
    evaluate_record_dict,
    finalize_processed_rows,
    load_record_dicts_from_jsonl,
    write_engine_outputs,
)


def run_local_engine(config: EngineConfig) -> dict[str, object]:
    record_dicts = load_record_dicts_from_jsonl(config.input_dir)
    processed = [evaluate_record_dict(record_dict) for record_dict in record_dicts]
    kept_records, dropped, source_counts = finalize_processed_rows(processed)
    return write_engine_outputs(
        config=config,
        raw_record_count=len(record_dicts),
        kept_records=kept_records,
        dropped=dropped,
        source_counts=source_counts,
        warnings=[],
    )

