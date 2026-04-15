from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Phase1WorkflowTest(unittest.TestCase):
    def test_phase1_run_local_release_layout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-phase1-") as data_root:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "src")
            cmd = [
                sys.executable,
                "-m",
                "lattice",
                "phase1-run",
                "--data-root",
                data_root,
                "--registry",
                str(ROOT / "configs" / "source_registry.json"),
                "--domain",
                "materials",
                "--release-name",
                "phase1-test",
                "--source",
                "openalex",
                "--source",
                "arxiv",
                "--source",
                "pubchem",
                "--query",
                "solid state battery electrolyte",
                "--compound",
                "lithium iron phosphate",
                "--compound",
                "lithium cobalt oxide",
                "--limit",
                "1",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["release_name"], "phase1-test")
            self.assertTrue(Path(payload["paths"]["raw"]).exists())
            self.assertTrue(Path(payload["paths"]["bronze"]).exists())
            self.assertTrue(Path(payload["paths"]["silver"]).exists())
            self.assertTrue(Path(payload["paths"]["gold"]).exists())
            self.assertTrue(Path(payload["paths"]["manifests"]).exists())
            self.assertIn("fetch", payload)
            self.assertIn("bronze", payload)
            self.assertIn("silver", payload)
            self.assertIn("gold", payload)
            self.assertGreaterEqual(payload["fetch"]["counts"]["pubchem"], 1)


if __name__ == "__main__":
    unittest.main()
