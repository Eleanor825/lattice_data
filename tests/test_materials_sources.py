from __future__ import annotations

import json
import os
from socket import timeout as SocketTimeout
import subprocess
import sys
import tempfile
import unittest
from urllib.error import URLError
from pathlib import Path

from lattice.sources.materials_project import resolve_materials_project_api_key
from lattice.sources.nomad import fetch_nomad_materials
from lattice.sources.oqmd import fetch_oqmd_structures

ROOT = Path(__file__).resolve().parents[1]


class MaterialsSourceTest(unittest.TestCase):
    def test_oqmd_fetch_returns_structured_records(self) -> None:
        try:
            rows = fetch_oqmd_structures(["Li", "O"], limit=1, domain="materials")
        except (TimeoutError, SocketTimeout, URLError) as exc:
            self.skipTest(f"OQMD fetch unavailable during test run: {exc}")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "oqmd")
        self.assertIn("chemical_formula_reduced", rows[0]["payload"]["fields"])
        self.assertIn("band_gap", rows[0]["payload"]["fields"])

    def test_nomad_fetch_returns_structured_records(self) -> None:
        try:
            rows = fetch_nomad_materials(["Li", "O"], limit=1, domain="materials")
        except (TimeoutError, SocketTimeout, URLError) as exc:
            self.skipTest(f"NOMAD fetch unavailable during test run: {exc}")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "nomad")
        self.assertIn("chemical_formula_reduced", rows[0]["payload"]["fields"])

    def test_nomad_can_compile_into_sft_target(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory(prefix="lattice-nomad-target-") as tmp:
            cmd = [
                sys.executable,
                "-m",
                "lattice",
                "build-target",
                "--input",
                str(ROOT / "examples" / "materials" / "raw"),
                "--output",
                str(Path(tmp) / "out"),
                "--target-spec",
                str(ROOT / "examples" / "targets" / "sft_dataset.yaml"),
                "--fetch-sources-first",
                "--registry",
                str(ROOT / "configs" / "source_registry.json"),
                "--source",
                "nomad",
                "--element",
                "Li",
                "--element",
                "O",
                "--limit",
                "1",
            ]
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            except subprocess.CalledProcessError as exc:
                error_text = (exc.stderr or "") + "\n" + (exc.stdout or "")
                if "timed out" in error_text.lower() or "timeout" in error_text.lower():
                    self.skipTest(f"NOMAD target build unavailable during test run: {error_text.strip()}")
                raise
            payload = json.loads(result.stdout)
            if payload.get("fetch", {}).get("counts", {}).get("nomad", 0) == 0:
                self.skipTest("NOMAD target build returned zero fetched rows during this run.")
            self.assertGreaterEqual(payload["output_counts"]["instruction_samples"], 1)

    def test_materials_project_key_resolution_is_optional(self) -> None:
        value = resolve_materials_project_api_key()
        self.assertTrue(value is None or isinstance(value, str))

    def test_materials_project_gracefully_skips_without_key(self) -> None:
        from lattice.sources.materials_project import fetch_materials_project_materials

        rows, warnings = fetch_materials_project_materials(["Li", "O"], limit=1, domain="materials")
        if resolve_materials_project_api_key():
            self.assertGreaterEqual(len(rows), 1)
        else:
            self.assertEqual(rows, [])
            self.assertTrue(any("MP_API_KEY" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
