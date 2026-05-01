from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SftTargetTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_sft_target_outputs_grounded_instruction_samples(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-sft-target-") as tmp:
            output_dir = Path(tmp) / "out"
            cmd = [
                sys.executable,
                "-m",
                "lattice",
                "build-target",
                "--input",
                str(ROOT / "examples" / "materials" / "raw"),
                "--output",
                str(output_dir),
                "--target-spec",
                str(ROOT / "examples" / "targets" / "sft_dataset.yaml"),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            rows = [
                json.loads(line)
                for line in (output_dir / "outputs" / "instruction_samples.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertGreater(len(rows), 0)
            task_types = {row["task_type"] for row in rows}
            self.assertIn("grounded_summarization", task_types)
            self.assertIn("property_listing", task_types)
            for row in rows:
                self.assertIn("instruction", row)
                self.assertIn("input", row)
                self.assertIn("output", row)
                self.assertIn("evidence", row)
                self.assertIn("sft_fitness", row)
                self.assertIn("evidence_completeness", row)
                self.assertIn("provenance_chain", row)
                self.assertTrue(row["source_record_id"])
            self.assertEqual(manifest["target_type"], "sft_dataset")
            self.assertGreater(manifest["output_counts"]["instruction_samples"], 0)


if __name__ == "__main__":
    unittest.main()
