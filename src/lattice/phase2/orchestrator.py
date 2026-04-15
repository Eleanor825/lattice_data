from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lattice.engines import EngineConfig, run_engine_compile
from lattice.phase2.providers import ModelBackendConfig, run_backend_workflow
from lattice.sources.common import timestamp_now
from lattice.utils import ensure_dir, write_json


@dataclass(slots=True)
class Phase2Config:
    workflow: str
    engine: str
    input_dir: str
    output_dir: str
    run_name: str
    model_backend: str
    model_name: str
    compiled_input: bool = True
    provider: str = "local"
    model_family: str = "open"
    api_base: str = ""
    api_key_env: str = ""
    domain: str = "materials"
    checkpoint_dir: str = ""
    epochs: int = 1
    batch_size: int = 2
    learning_rate: float = 3e-4
    max_length: int = 192
    hidden_size: int = 96


def run_phase2_pipeline(config: Phase2Config) -> dict[str, Any]:
    output_dir = ensure_dir(config.output_dir)
    prepared_dir = Path(config.input_dir)

    if not config.compiled_input:
        prepared_dir = ensure_dir(output_dir / "prepared")
        run_engine_compile(
            EngineConfig(
                input_dir=config.input_dir,
                output_dir=str(prepared_dir),
                domain=config.domain,
                dataset_name=f"{config.run_name}-prepared",
                engine=config.engine,
            )
        )

    backend_result = run_backend_workflow(
        workflow=config.workflow,
        dataset_dir=str(prepared_dir),
        output_dir=str(output_dir / "training"),
        run_name=config.run_name,
        checkpoint_dir=config.checkpoint_dir,
        backend_config=ModelBackendConfig(
            backend=config.model_backend,
            model_name=config.model_name,
            provider=config.provider,
            model_family=config.model_family,
            api_base=config.api_base,
            api_key_env=config.api_key_env,
        ),
        epochs=config.epochs,
        batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        max_length=config.max_length,
        hidden_size=config.hidden_size,
    )

    manifest = {
        "generated_at": timestamp_now(),
        "workflow": config.workflow,
        "engine": config.engine,
        "run_name": config.run_name,
        "input_dir": str(Path(config.input_dir).resolve()),
        "prepared_dir": str(prepared_dir.resolve()),
        "output_dir": str(Path(output_dir).resolve()),
        "config": asdict(config),
        "backend_result": backend_result,
    }
    write_json(output_dir / "phase2_manifest.json", manifest)
    return manifest

