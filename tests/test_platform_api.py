from __future__ import annotations

import json
import os
import sqlite3
import time
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from lattice.platform.server import create_app


ROOT = Path(__file__).resolve().parents[1]


class PlatformApiTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        java_home = Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
        if java_home.exists():
            env["JAVA_HOME"] = str(java_home)
            env["PATH"] = f"{java_home / 'bin'}:{env.get('PATH', '')}"
        return env

    def test_platform_api_lists_and_detail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-api-") as tmp:
            db_path = Path(tmp) / "registry.db"
            phase2_out = Path(tmp) / "phase2"
            cmd = [
                sys.executable, "-m", "lattice", "phase2-run",
                "--workflow", "finetune",
                "--engine", "pandas",
                "--input", str(ROOT / "examples" / "training" / "demo_dataset"),
                "--output", str(phase2_out),
                "--run-name", "api-demo",
                "--model-backend", "local_tiny",
                "--model-name", "tiny-local",
                "--compiled-input",
                "--registry-db", str(db_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())

            app = create_app(str(db_path))
            client = TestClient(app)

            runs = client.get("/runs")
            self.assertEqual(runs.status_code, 200)
            run_items = runs.json()
            self.assertGreaterEqual(len(run_items), 1)
            run_id = run_items[0]["run_id"]

            run_detail = client.get(f"/runs/{run_id}")
            self.assertEqual(run_detail.status_code, 200)
            self.assertEqual(run_detail.json()["run_id"], run_id)

            bad_transition = client.patch(f"/runs/{run_id}/status", json={"status": "prepared"})
            self.assertEqual(bad_transition.status_code, 400)

            backends = client.get("/backends")
            self.assertEqual(backends.status_code, 200)
            self.assertGreaterEqual(len(backends.json()), 1)

            datasets = client.get("/datasets")
            self.assertEqual(datasets.status_code, 200)
            self.assertGreaterEqual(len(datasets.json()), 0)

    def test_platform_api_submission_endpoints(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-api-submit-") as tmp:
            db_path = Path(tmp) / "registry.db"
            app = create_app(str(db_path))
            client = TestClient(app)

            phase1 = client.post(
                "/phase1-runs",
                json={
                    "data_root": str(Path(tmp) / "phase1"),
                    "registry_path": str(ROOT / "configs" / "source_registry.json"),
                    "domain": "materials",
                    "release_name": "api-phase1",
                    "sources": ["pubchem"],
                    "compounds": ["lithium iron phosphate"],
                    "limit": 1,
                },
            )
            self.assertEqual(phase1.status_code, 200)
            phase1_run_id = phase1.json()["run_id"]

            phase2 = client.post(
                "/phase2-runs",
                json={
                    "workflow": "finetune",
                    "engine": "pandas",
                    "input_dir": str(ROOT / "examples" / "training" / "demo_dataset"),
                    "output_dir": str(Path(tmp) / "phase2"),
                    "run_name": "api-phase2",
                    "model_backend": "local_tiny",
                    "model_name": "tiny-local",
                    "compiled_input": True,
                },
            )
            self.assertEqual(phase2.status_code, 200)
            phase2_run_id = phase2.json()["run_id"]

            for _ in range(20):
                r1 = client.get(f"/runs/{phase1_run_id}").json()
                r2 = client.get(f"/runs/{phase2_run_id}").json()
                if r1["status"] == "completed" and r2["status"] == "completed":
                    break
                time.sleep(0.2)

            self.assertEqual(client.get(f"/runs/{phase1_run_id}").json()["status"], "completed")
            self.assertEqual(client.get(f"/runs/{phase2_run_id}").json()["status"], "completed")

            rerun = client.post(f"/runs/{phase2_run_id}/rerun")
            self.assertEqual(rerun.status_code, 200)
            rerun_id = rerun.json()["run_id"]

            for _ in range(20):
                rerun_row = client.get(f"/runs/{rerun_id}").json()
                if rerun_row["status"] == "completed":
                    break
                time.sleep(0.2)

            rerun_row = client.get(f"/runs/{rerun_id}").json()
            self.assertEqual(rerun_row["status"], "completed")
            self.assertEqual(rerun_row["payload"]["retry_parent_run_id"], phase2_run_id)


if __name__ == "__main__":
    unittest.main()
