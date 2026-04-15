from __future__ import annotations

from pathlib import Path
from typing import Any

from lattice.platform.registry import PlatformRegistry
from lattice.platform.specs import BackendRef, DatasetRef, ExecutionRef, WorkflowSpec
from lattice.sources.common import timestamp_now
from lattice.utils import read_json, stable_hash


def sync_phase1_manifest(db_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    payload = read_json(manifest_path)
    registry = PlatformRegistry(db_path)
    try:
        for section in ("bronze", "gold"):
            section_payload = payload[section]
            dataset_id = stable_hash(f"{section}:{section_payload['dataset_name']}:{section_payload['output_dir']}")
            registry.register_dataset(
                dataset_id=dataset_id,
                phase="phase1",
                dataset_name=section_payload["dataset_name"],
                domain=section_payload["domain"],
                manifest_path=str(Path(section_payload["output_dir"]) / "reports" / "manifest.json"),
                output_dir=section_payload["output_dir"],
                generated_at=payload["generated_at"],
                payload=section_payload,
            )

        run_id = stable_hash(f"phase1:{payload['release_name']}:{payload['paths']['root']}")
        workflow_spec = WorkflowSpec(
            phase="phase1",
            workflow="phase1-release",
            run_name=payload["release_name"],
            dataset=DatasetRef(
                path=payload["paths"]["raw"],
                compiled=False,
                domain=payload["domain"],
            ),
            backend=BackendRef(
                backend="none",
                model_name="none",
                provider="none",
                model_family="none",
            ),
            execution=ExecutionRef(engine="multi", local_only=False),
        )
        registry.register_run(
            run_id=run_id,
            phase="phase1",
            workflow="phase1-release",
            engine="multi",
            model_backend="none",
            model_family="none",
            status="completed",
            domain=payload["domain"],
            run_name=payload["release_name"],
            input_dir=payload["paths"]["raw"],
            output_dir=payload["paths"]["gold"],
            generated_at=payload["generated_at"],
            payload={"manifest": payload, "workflow_spec": workflow_spec.to_dict()},
        )
        return {"status": "ok", "run_id": run_id}
    finally:
        registry.close()


def prepare_phase2_run(db_path: str | Path, spec: WorkflowSpec, *, input_dir: str, output_dir: str) -> dict[str, Any]:
    registry = PlatformRegistry(db_path)
    try:
        backend_id = stable_hash(f"{spec.backend.backend}:{spec.backend.provider}:{spec.backend.model_name}")
        registry.register_backend(backend_id=backend_id, payload=spec.backend.to_dict())
        run_id = stable_hash(f"phase2:{spec.run_name}:{spec.workflow}:{output_dir}")
        registry.register_run(
            run_id=run_id,
            phase=spec.phase,
            workflow=spec.workflow,
            engine=spec.execution.engine,
            model_backend=spec.backend.backend,
            model_family=spec.backend.model_family,
            status="prepared",
            domain=spec.dataset.domain,
            run_name=spec.run_name,
            input_dir=input_dir,
            output_dir=output_dir,
            generated_at=timestamp_now(),
            payload={"workflow_spec": spec.to_dict()},
        )
        return {"status": "ok", "run_id": run_id, "backend_id": backend_id}
    finally:
        registry.close()


def sync_phase2_manifest(db_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    payload = read_json(manifest_path)
    backend = payload["backend_result"]["backend"]
    registry = PlatformRegistry(db_path)
    try:
        backend_id = stable_hash(f"{backend['backend']}:{backend['provider']}:{backend['model_name']}")
        registry.register_backend(backend_id=backend_id, payload=backend)
        run_id = stable_hash(f"phase2:{payload['run_name']}:{payload['workflow']}:{payload['output_dir']}")
        workflow_spec = WorkflowSpec(
            phase="phase2",
            workflow=payload["workflow"],
            run_name=payload["run_name"],
            dataset=DatasetRef(
                path=payload["input_dir"],
                compiled=bool(payload["config"].get("compiled_input", False)),
                domain=payload["config"]["domain"],
            ),
            backend=BackendRef(**backend),
            execution=ExecutionRef(
                engine=payload["engine"],
                local_only=payload["engine"] in {"local", "pandas"},
            ),
            checkpoint_dir=payload["config"].get("checkpoint_dir", ""),
            params={
                "epochs": payload["config"].get("epochs", 1),
                "batch_size": payload["config"].get("batch_size", 2),
                "learning_rate": payload["config"].get("learning_rate", 3e-4),
            },
        )
        row = registry.conn.execute("SELECT run_id FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            registry.register_run(
                run_id=run_id,
                phase="phase2",
                workflow=payload["workflow"],
                engine=payload["engine"],
                model_backend=backend["backend"],
                model_family=backend["model_family"],
                status="completed",
                domain=payload["config"]["domain"],
                run_name=payload["run_name"],
                input_dir=payload["input_dir"],
                output_dir=payload["output_dir"],
                generated_at=payload["generated_at"],
                payload={"manifest": payload, "workflow_spec": workflow_spec.to_dict()},
            )
        else:
            registry.update_run_status(
                run_id,
                "completed",
                payload={"manifest": payload, "workflow_spec": workflow_spec.to_dict()},
            )
        return {"status": "ok", "run_id": run_id, "backend_id": backend_id}
    finally:
        registry.close()
