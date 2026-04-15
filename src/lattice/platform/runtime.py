from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lattice.platform.specs import BackendRef, DatasetRef, ExecutionRef, WorkflowSpec

if TYPE_CHECKING:
    from lattice.phase2 import Phase2Config
    from lattice.workflows import Phase1Config


def build_phase1_spec(config: Phase1Config) -> WorkflowSpec:
    return WorkflowSpec(
        phase="phase1",
        workflow="phase1-release",
        run_name=config.release_name,
        dataset=DatasetRef(path=config.data_root, compiled=False, domain=config.domain),
        backend=BackendRef(backend="none", model_name="none", provider="none", model_family="none"),
        execution=ExecutionRef(engine="multi", local_only=False),
        params={
            "data_root": config.data_root,
            "registry_path": config.registry_path,
            "query": config.query,
            "elements": config.elements,
            "compounds": config.compounds,
            "sources": config.sources,
            "limit": config.limit,
            "include_optional_sources": config.include_optional_sources,
        },
    )


def build_phase2_spec(config: Phase2Config) -> WorkflowSpec:
    return WorkflowSpec(
        phase="phase2",
        workflow=config.workflow,
        run_name=config.run_name,
        dataset=DatasetRef(path=config.input_dir, compiled=config.compiled_input, domain=config.domain),
        backend=BackendRef(
            backend=config.model_backend,
            model_name=config.model_name,
            provider=config.provider,
            model_family=config.model_family,
            api_base=config.api_base,
            api_key_env=config.api_key_env,
        ),
        execution=ExecutionRef(engine=config.engine, local_only=config.engine in {"local", "pandas"}),
        checkpoint_dir=config.checkpoint_dir,
        params={
            "input_dir": config.input_dir,
            "output_dir": config.output_dir,
            "compiled_input": config.compiled_input,
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "max_length": config.max_length,
            "hidden_size": config.hidden_size,
        },
    )


def workflow_spec_from_dict(payload: dict[str, Any]) -> WorkflowSpec:
    return WorkflowSpec.from_dict(payload)


def config_snapshot(config: Phase1Config | Phase2Config) -> dict[str, Any]:
    return asdict(config)


def phase1_config_from_snapshot(payload: dict[str, Any], *, registry_db: str = "") -> Phase1Config:
    from lattice.workflows import Phase1Config

    snapshot = dict(payload)
    if registry_db:
        snapshot["registry_db"] = registry_db
    return Phase1Config(**snapshot)


def phase2_config_from_snapshot(payload: dict[str, Any], *, registry_db: str = "") -> Phase2Config:
    from lattice.phase2 import Phase2Config

    snapshot = dict(payload)
    if registry_db:
        snapshot["registry_db"] = registry_db
    return Phase2Config(**snapshot)


def make_retry_suffix(retry_index: int) -> str:
    return f"retry-{retry_index}"


def with_retry_suffix(value: str, retry_index: int) -> str:
    suffix = make_retry_suffix(retry_index)
    return f"{value}-{suffix}"


def derive_retry_phase1_config(payload: dict[str, Any], *, registry_db: str, retry_index: int) -> Phase1Config:
    config = phase1_config_from_snapshot(payload, registry_db=registry_db)
    config.release_name = with_retry_suffix(config.release_name, retry_index)
    return config


def derive_retry_phase2_config(payload: dict[str, Any], *, registry_db: str, retry_index: int) -> Phase2Config:
    config = phase2_config_from_snapshot(payload, registry_db=registry_db)
    config.run_name = with_retry_suffix(config.run_name, retry_index)
    config.output_dir = with_retry_suffix(str(Path(config.output_dir)), retry_index)
    return config


def run_workflow_spec(spec: WorkflowSpec, *, registry_db: str = "") -> dict[str, Any]:
    if spec.phase == "phase1":
        from lattice.workflows import Phase1Config, run_phase1_pipeline

        config = Phase1Config(
            data_root=str(spec.params["data_root"]),
            registry_path=str(spec.params["registry_path"]),
            domain=spec.dataset.domain,
            release_name=spec.run_name,
            query=str(spec.params.get("query", "solid state battery electrolyte")),
            elements=[str(item) for item in spec.params.get("elements", ["Li", "O"])],
            compounds=[str(item) for item in spec.params.get("compounds", ["lithium iron phosphate", "lithium cobalt oxide"])],
            sources=[str(item) for item in spec.params.get("sources", [])],
            limit=int(spec.params.get("limit", 3)),
            include_optional_sources=bool(spec.params.get("include_optional_sources", False)),
            registry_db=registry_db,
        )
        return run_phase1_pipeline(config)

    from lattice.phase2 import Phase2Config, run_phase2_pipeline

    config = Phase2Config(
        workflow=spec.workflow,
        engine=spec.execution.engine,
        input_dir=str(spec.params["input_dir"]),
        output_dir=str(spec.params["output_dir"]),
        run_name=spec.run_name,
        model_backend=spec.backend.backend,
        model_name=spec.backend.model_name,
        compiled_input=bool(spec.params.get("compiled_input", spec.dataset.compiled)),
        provider=spec.backend.provider,
        model_family=spec.backend.model_family,
        api_base=spec.backend.api_base,
        api_key_env=spec.backend.api_key_env,
        domain=spec.dataset.domain,
        checkpoint_dir=spec.checkpoint_dir,
        registry_db=registry_db,
        epochs=int(spec.params.get("epochs", 1)),
        batch_size=int(spec.params.get("batch_size", 2)),
        learning_rate=float(spec.params.get("learning_rate", 3e-4)),
        max_length=int(spec.params.get("max_length", 192)),
        hidden_size=int(spec.params.get("hidden_size", 96)),
    )
    return run_phase2_pipeline(config)
