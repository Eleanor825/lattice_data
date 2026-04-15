from __future__ import annotations

import json

import pandas as pd

from lattice.engines.shared import (
    EngineConfig,
    evaluate_record_dict,
    finalize_processed_rows,
    load_record_dicts_from_jsonl,
    write_engine_outputs,
)


def run_pandas_engine(config: EngineConfig) -> dict[str, object]:
    record_dicts = load_record_dicts_from_jsonl(config.input_dir)
    if not record_dicts:
        return write_engine_outputs(
            config=config,
            raw_record_count=0,
            kept_records=[],
            dropped={},
            source_counts={},
            warnings=["No JSONL inputs found for pandas engine."],
        )

    df = pd.DataFrame({"record_json": record_dicts})
    processed_rows = [evaluate_record_dict(record) for record in df["record_json"].tolist()]
    kept_records, dropped, source_counts = finalize_processed_rows(processed_rows)
    return write_engine_outputs(
        config=config,
        raw_record_count=len(record_dicts),
        kept_records=kept_records,
        dropped=dropped,
        source_counts=source_counts,
        warnings=[],
    )


def pandas_smoke_check() -> dict[str, object]:
    try:
        df = pd.DataFrame({"x": [1, 2, 3]})
        count = int(df["x"].count())
        return {"available": True, "detail": f"Pandas smoke test passed with count={count}."}
    except Exception as exc:
        return {"available": False, "detail": str(exc)}

