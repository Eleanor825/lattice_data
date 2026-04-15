from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from lattice.platform.state import can_transition
from lattice.utils import ensure_dir


class PlatformRegistry:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        ensure_dir(self.db_path.parent)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                phase TEXT NOT NULL,
                workflow TEXT NOT NULL,
                engine TEXT NOT NULL,
                model_backend TEXT NOT NULL,
                model_family TEXT NOT NULL,
                status TEXT NOT NULL,
                domain TEXT NOT NULL,
                run_name TEXT NOT NULL,
                input_dir TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                phase TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                manifest_path TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS backends (
                backend_id TEXT PRIMARY KEY,
                backend_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_family TEXT NOT NULL,
                api_base TEXT NOT NULL,
                api_key_env TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def register_dataset(self, *, dataset_id: str, phase: str, dataset_name: str, domain: str, manifest_path: str, output_dir: str, generated_at: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO datasets (
                dataset_id, phase, dataset_name, domain, manifest_path, output_dir, generated_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                phase,
                dataset_name,
                domain,
                manifest_path,
                output_dir,
                generated_at,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def register_backend(self, *, backend_id: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO backends (
                backend_id, backend_name, model_name, provider, model_family, api_base, api_key_env, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backend_id,
                payload.get("backend", ""),
                payload.get("model_name", ""),
                payload.get("provider", ""),
                payload.get("model_family", ""),
                payload.get("api_base", ""),
                payload.get("api_key_env", ""),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def register_run(
        self,
        *,
        run_id: str,
        phase: str,
        workflow: str,
        engine: str,
        model_backend: str,
        model_family: str,
        status: str,
        domain: str,
        run_name: str,
        input_dir: str,
        output_dir: str,
        generated_at: str,
        payload: dict[str, Any],
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO runs (
                run_id, phase, workflow, engine, model_backend, model_family,
                status, domain, run_name, input_dir, output_dir, generated_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                phase,
                workflow,
                engine,
                model_backend,
                model_family,
                status,
                domain,
                run_name,
                input_dir,
                output_dir,
                generated_at,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def update_run_status(self, run_id: str, status: str, payload: dict[str, Any] | None = None) -> None:
        row = self.conn.execute("SELECT status, payload_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        current_status = str(row["status"])
        if not can_transition(current_status, status):  # type: ignore[arg-type]
            raise ValueError(f"Invalid run status transition: {current_status} -> {status}")
        payload_json = row["payload_json"]
        current_payload = json.loads(payload_json)
        if payload is not None:
            current_payload.update(payload)
        self.conn.execute(
            "UPDATE runs SET status = ?, payload_json = ? WHERE run_id = ?",
            (status, json.dumps(current_payload, ensure_ascii=False), run_id),
        )
        self.conn.commit()

    def list_runs(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM runs ORDER BY generated_at DESC").fetchall()
        return [dict(row) for row in rows]

    def list_datasets(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM datasets ORDER BY generated_at DESC").fetchall()
        return [dict(row) for row in rows]

    def list_backends(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM backends ORDER BY backend_name, model_name").fetchall()
        return [dict(row) for row in rows]
