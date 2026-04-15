from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Phase2WorkflowTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        java_home = Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
        if java_home.exists():
            env["JAVA_HOME"] = str(java_home)
            env["PATH"] = f"{java_home / 'bin'}:{env.get('PATH', '')}"
        return env

    def test_phase2_local_open_backend(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-phase2-open-") as tmp:
            output_dir = Path(tmp) / "run"
            cmd = [
                sys.executable, "-m", "lattice", "phase2-run",
                "--workflow", "finetune",
                "--engine", "pandas",
                "--input", str(ROOT / "examples" / "training" / "demo_dataset"),
                "--output", str(output_dir),
                "--run-name", "phase2-open-demo",
                "--model-backend", "local_tiny",
                "--model-name", "tiny-local",
                "--compiled-input",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["workflow"], "finetune")
            self.assertEqual(payload["backend_result"]["mode"], "local_train")

    def test_phase2_closed_connector(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-phase2-closed-") as tmp:
            output_dir = Path(tmp) / "run"
            cmd = [
                sys.executable, "-m", "lattice", "phase2-run",
                "--workflow", "posttrain",
                "--engine", "pandas",
                "--input", str(ROOT / "examples" / "training" / "demo_dataset"),
                "--output", str(output_dir),
                "--run-name", "phase2-closed-demo",
                "--model-backend", "external_connector",
                "--model-name", "closed-provider-model",
                "--provider", "openai_compatible",
                "--model-family", "closed",
                "--compiled-input",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["backend_result"]["mode"], "connector_request")
            self.assertEqual(payload["backend_result"]["backend"]["model_family"], "closed")


if __name__ == "__main__":
    unittest.main()
