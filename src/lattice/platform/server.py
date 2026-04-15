from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lattice.platform.registry import PlatformRegistry


class RunStatusUpdate(BaseModel):
    status: str


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
