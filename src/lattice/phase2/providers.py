from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.sources.common import timestamp_now
from lattice.training import TrainingConfig, run_training_workflow
from lattice.utils import ensure_dir, write_json


@dataclass(slots=True)
class ModelBackendConfig:
    backend: str
    model_name: str
    provider: str = "local"
    model_family: str = "open"
    api_base: str = ""
    api_key_env: str = ""


def run_backend_workflow(
    *,
    workflow: str,
    dataset_dir: str,
    output_dir: str,
    run_name: str,
    checkpoint_dir: str,
    backend_config: ModelBackendConfig,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    max_length: int,
    hidden_size: int,
) -> dict[str, Any]:
    if backend_config.backend == "local_tiny":
        result = run_training_workflow(
            TrainingConfig(
                workflow=workflow,
                input_dir=dataset_dir,
                output_dir=output_dir,
                run_name=run_name,
                checkpoint_dir=checkpoint_dir,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                max_length=max_length,
                hidden_size=hidden_size,
            )
        )
        return {
            "mode": "local_train",
            "backend": asdict(backend_config),
            "result": asdict(result),
        }

    ensure_dir(output_dir)
    connector_manifest = {
        "generated_at": timestamp_now(),
        "mode": "connector_request",
        "workflow": workflow,
        "run_name": run_name,
        "dataset_dir": str(Path(dataset_dir).resolve()),
        "checkpoint_dir": str(Path(checkpoint_dir).resolve()) if checkpoint_dir else "",
        "backend": asdict(backend_config),
        "status": "prepared",
        "note": (
            "This run is prepared for an external model provider. "
            "Closed models are supported through a unified connector manifest rather than local weight training."
        ),
    }
    write_json(Path(output_dir) / "connector_manifest.json", connector_manifest)
    return connector_manifest

