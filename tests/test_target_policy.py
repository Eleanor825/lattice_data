from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TargetPolicyTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def _write_spec(self, path: Path, license_policy: str) -> None:
        path.write_text(
            "\n".join(
                [
                    "target_type: rag_corpus",
                    "domain: materials",
                    "consumer: policy_test",
                    f"license_policy: {license_policy}",
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

    def test_policy_modes_produce_explainable_differences(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-policy-target-") as tmp:
            research_spec = Path(tmp) / "research.yaml"
            exclude_unknown_spec = Path(tmp) / "exclude.yaml"
            self._write_spec(research_spec, "research_only")
            self._write_spec(exclude_unknown_spec, "exclude_unknown_license")

            def run_build(spec_path: Path, out_dir: Path) -> dict:
                cmd = [
                    sys.executable,
                    "-m",
                    "lattice",
                    "build-target",
                    "--input",
                    str(ROOT / "examples" / "materials" / "raw"),
                    "--output",
                    str(out_dir),
                    "--target-spec",
                    str(spec_path),
                ]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
                return json.loads(result.stdout)

            research_manifest = run_build(research_spec, Path(tmp) / "research")
            exclude_manifest = run_build(exclude_unknown_spec, Path(tmp) / "exclude")

            self.assertGreaterEqual(research_manifest["kept_record_count"], exclude_manifest["kept_record_count"])
            self.assertIn("license_policy", research_manifest)
            self.assertIn("license_policy", exclude_manifest)
            self.assertIn("dropped_records", exclude_manifest)
            self.assertGreaterEqual(exclude_manifest["dropped_records"].get("policy_unknown_license", 0), 0)


if __name__ == "__main__":
    unittest.main()
