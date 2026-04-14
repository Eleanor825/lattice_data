from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EngineTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_local_engine_compile(self) -> None:
        output_dir = Path(tempfile.mkdtemp(prefix="lattice-engine-local-"))
        cmd = [
            sys.executable,
            "-m",
            "lattice",
            "engine-compile",
            "--engine",
            "local",
            "--input",
            str(ROOT / "examples" / "runtime" / "raw"),
            "--output",
            str(output_dir),
            "--domain",
            "materials",
            "--dataset-name",
            "Lattice-Runtime-Local",
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
        self.assertIn('"engine": "local"', result.stdout)

    def test_engine_check_command(self) -> None:
        cmd = [sys.executable, "-m", "lattice", "engine-check"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
        self.assertIn('"local"', result.stdout)
        self.assertIn('"spark"', result.stdout)
        self.assertIn('"flink"', result.stdout)


if __name__ == "__main__":
    unittest.main()
