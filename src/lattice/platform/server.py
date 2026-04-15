from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lattice.platform.jobs import rerun_job, submit_phase1_job, submit_phase2_job
from lattice.platform.registry import PlatformRegistry


class RunStatusUpdate(BaseModel):
    status: str


class Phase1SubmitRequest(BaseModel):
    data_root: str
    registry_path: str
    domain: str = "materials"
    release_name: str
    query: str = "solid state battery electrolyte"
    elements: list[str] = ["Li", "O"]
    compounds: list[str] = ["lithium iron phosphate", "lithium cobalt oxide"]
    sources: list[str] = []
    limit: int = 3
    include_optional_sources: bool = False


class Phase2SubmitRequest(BaseModel):
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


def create_app(db_path: str) -> FastAPI:
    registry = PlatformRegistry(db_path)
    app = FastAPI(title="Lattice Platform API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True}

    @app.get("/runs")
    def runs() -> list[dict[str, object]]:
        return registry.list_runs()

    @app.get("/runs/{run_id}")
    def run_detail(run_id: str) -> dict[str, object]:
        row = registry.get_run(run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return row

    @app.patch("/runs/{run_id}/status")
    def run_status(run_id: str, payload: RunStatusUpdate) -> dict[str, object]:
        try:
            registry.update_run_status(run_id, payload.status)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        row = registry.get_run(run_id)
        assert row is not None
        return row

    @app.post("/phase1-runs")
    def submit_phase1(payload: Phase1SubmitRequest) -> dict[str, object]:
        from lattice.workflows import Phase1Config

        config = Phase1Config(
            data_root=payload.data_root,
            registry_path=payload.registry_path,
            domain=payload.domain,
            release_name=payload.release_name,
            query=payload.query,
            elements=payload.elements,
            compounds=payload.compounds,
            sources=payload.sources,
            limit=payload.limit,
            include_optional_sources=payload.include_optional_sources,
            registry_db=db_path,
        )
        return submit_phase1_job(config)

    @app.post("/phase2-runs")
    def submit_phase2(payload: Phase2SubmitRequest) -> dict[str, object]:
        from lattice.phase2 import Phase2Config

        config = Phase2Config(
            workflow=payload.workflow,
            engine=payload.engine,
            input_dir=payload.input_dir,
            output_dir=payload.output_dir,
            run_name=payload.run_name,
            model_backend=payload.model_backend,
            model_name=payload.model_name,
            compiled_input=payload.compiled_input,
            provider=payload.provider,
            model_family=payload.model_family,
            api_base=payload.api_base,
            api_key_env=payload.api_key_env,
            domain=payload.domain,
            checkpoint_dir=payload.checkpoint_dir,
            registry_db=db_path,
            epochs=payload.epochs,
            batch_size=payload.batch_size,
            learning_rate=payload.learning_rate,
            max_length=payload.max_length,
            hidden_size=payload.hidden_size,
        )
        return submit_phase2_job(config)

    @app.post("/runs/{run_id}/rerun")
    def rerun(run_id: str) -> dict[str, object]:
        try:
            return rerun_job(db_path, run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/datasets")
    def datasets() -> list[dict[str, object]]:
        return registry.list_datasets()

    @app.get("/datasets/{dataset_id}")
    def dataset_detail(dataset_id: str) -> dict[str, object]:
        row = registry.get_dataset(dataset_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return row

    @app.get("/backends")
    def backends() -> list[dict[str, object]]:
        return registry.list_backends()

    @app.get("/backends/{backend_id}")
    def backend_detail(backend_id: str) -> dict[str, object]:
        row = registry.get_backend(backend_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Backend not found")
        return row

    return app
