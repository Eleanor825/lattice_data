from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceGovernanceTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def _write_spec(self, path: Path, policy: str) -> None:
        path.write_text(
            "\n".join(
                [
                    "target_type: rag_corpus",
                    "domain: materials",
                    "consumer: governance_test",
                    f"license_policy: {policy}",
                    "quality_objectives:",
                    "  - grounded",
                    "constraints:",
                    "  chunk_size: 500",
                    "target_config:",
                    "  chunk_size: 500",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_manifest_includes_source_governance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-source-governance-") as tmp:
            spec = Path(tmp) / "spec.yaml"
            self._write_spec(spec, "research_only")
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
                str(spec),
                "--registry",
                str(ROOT / "configs" / "source_registry.json"),
                "--source",
                "openalex",
                "--source",
                "pubchem",
                "--source",
                "unknown_source",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            self.assertIn("source_governance", manifest)
            self.assertEqual(len(manifest["source_governance"]), 3)
            self.assertTrue(any(row["maturity"] == "production_candidate" for row in manifest["source_governance"]))
            self.assertTrue(any("Unknown source in governance registry" in warning for warning in manifest["warnings"]))

    def test_commercial_safe_marks_source_compatibility(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-source-safe-") as tmp:
            spec = Path(tmp) / "safe.yaml"
            self._write_spec(spec, "commercial_safe")
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
                str(spec),
                "--registry",
                str(ROOT / "configs" / "source_registry.json"),
                "--source",
                "openalex",
                "--source",
                "materials_project",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            self.assertTrue(all("policy_compatible" in row for row in manifest["source_governance"]))


if __name__ == "__main__":
    unittest.main()
