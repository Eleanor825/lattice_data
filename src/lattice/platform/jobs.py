from __future__ import annotations

from dataclasses import replace
import threading
from typing import Any
from pathlib import Path

from lattice.phase2 import Phase2Config, run_phase2_pipeline
from lattice.platform.registry import PlatformRegistry
from lattice.platform.runtime import (
    build_phase1_spec,
    build_phase2_spec,
    config_snapshot,
    derive_retry_phase1_config,
    derive_retry_phase2_config,
)
from lattice.platform.sync import prepare_phase1_run, prepare_phase2_run
from lattice.platform.sync import sync_phase1_manifest, sync_phase2_manifest
from lattice.workflows import Phase1Config, run_phase1_pipeline


_threads: dict[str, threading.Thread] = {}


def _register_thread(run_id: str, thread: threading.Thread) -> None:
    _threads[run_id] = thread


def _attach_submission_payload(
    *,
    db_path: str,
    run_id: str,
    config_payload: dict[str, Any],
    workflow_spec: dict[str, Any],
    retry_parent_run_id: str = "",
    retry_index: int = 0,
) -> None:
    registry = PlatformRegistry(db_path)
    try:
        registry.update_run_status(
            run_id,
            "prepared",
            payload={
                "config": config_payload,
                "workflow_spec": workflow_spec,
                "retry_parent_run_id": retry_parent_run_id,
                "retry_index": retry_index,
            },
        )
    finally:
        registry.close()


def submit_phase1_job(config: Phase1Config, *, retry_parent_run_id: str = "", retry_index: int = 0) -> dict[str, Any]:
    spec = build_phase1_spec(config)
    prepare = prepare_phase1_run(
        config.registry_db,
        spec,
        input_dir=str(Path(config.data_root).expanduser().resolve()),
        output_dir=str(Path(config.data_root).expanduser().resolve()),
    )
    run_id = prepare["run_id"]
    _attach_submission_payload(
        db_path=config.registry_db,
        run_id=run_id,
        config_payload=config_snapshot(config),
        workflow_spec=spec.to_dict(),
        retry_parent_run_id=retry_parent_run_id,
        retry_index=retry_index,
    )

    def _runner() -> None:
        registry = PlatformRegistry(config.registry_db)
        try:
            registry.update_run_status(run_id, "running")
            run_config = replace(config, registry_db="")
            manifest = run_phase1_pipeline(run_config)
            manifest_path = Path(manifest["paths"]["manifests"]) / "phase1_manifest.json"
            sync_phase1_manifest(config.registry_db, manifest_path)
        except Exception as exc:
            registry.update_run_status(run_id, "failed", payload={"error": str(exc)})
        finally:
            registry.close()

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    _register_thread(run_id, thread)
    return {"run_id": run_id, "status": "prepared", "retry_parent_run_id": retry_parent_run_id}


def submit_phase2_job(config: Phase2Config, *, retry_parent_run_id: str = "", retry_index: int = 0) -> dict[str, Any]:
    spec = build_phase2_spec(config)
    prepare = prepare_phase2_run(
        config.registry_db,
        spec,
        input_dir=str(Path(config.input_dir).expanduser().resolve()),
        output_dir=str(Path(config.output_dir).expanduser().resolve()),
    )
    run_id = prepare["run_id"]
    _attach_submission_payload(
        db_path=config.registry_db,
        run_id=run_id,
        config_payload=config_snapshot(config),
        workflow_spec=spec.to_dict(),
        retry_parent_run_id=retry_parent_run_id,
        retry_index=retry_index,
    )

    def _runner() -> None:
        registry = PlatformRegistry(config.registry_db)
        try:
            registry.update_run_status(run_id, "running")
            run_config = replace(config, registry_db="")
            manifest = run_phase2_pipeline(run_config)
            manifest_path = Path(manifest["output_dir"]) / "phase2_manifest.json"
            sync_phase2_manifest(config.registry_db, manifest_path)
        except Exception as exc:
            registry.update_run_status(run_id, "failed", payload={"error": str(exc)})
        finally:
            registry.close()

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    _register_thread(run_id, thread)
    return {"run_id": run_id, "status": "prepared", "retry_parent_run_id": retry_parent_run_id}


def rerun_job(db_path: str, run_id: str) -> dict[str, Any]:
    registry = PlatformRegistry(db_path)
    try:
        row = registry.get_run(run_id)
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        payload = row.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("Run payload is missing or invalid.")
        config_payload = payload.get("config")
        if not isinstance(config_payload, dict):
            raise ValueError("Run does not include a reproducible config snapshot.")
        retry_index = int(payload.get("retry_index", 0)) + 1
        phase = str(row["phase"])
    finally:
        registry.close()

    if phase == "phase1":
        config = derive_retry_phase1_config(config_payload, registry_db=db_path, retry_index=retry_index)
        return submit_phase1_job(config, retry_parent_run_id=run_id, retry_index=retry_index)

    config = derive_retry_phase2_config(config_payload, registry_db=db_path, retry_index=retry_index)
    return submit_phase2_job(config, retry_parent_run_id=run_id, retry_index=retry_index)
