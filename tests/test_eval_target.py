from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EvalTargetTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_eval_target_outputs_judgeable_items(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-eval-target-") as tmp:
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
                str(ROOT / "examples" / "targets" / "eval_dataset.yaml"),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            rows = [
                json.loads(line)
                for line in (output_dir / "outputs" / "eval_items.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertGreater(len(rows), 0)
            eval_types = {row["eval_type"] for row in rows}
            self.assertIn("grounded_qa", eval_types)
            self.assertIn("property_extraction", eval_types)
            for row in rows:
                self.assertIn("prompt", row)
                self.assertIn("gold_answer", row)
                self.assertIn("gold_evidence", row)
                self.assertIn("rubric", row)
                self.assertIn("judgeability", row)
                self.assertIn("evidence_coverage", row)
                self.assertGreaterEqual(float(row["judgeability"]), 0.5)
                self.assertTrue(row["source_record_id"])
            self.assertEqual(manifest["target_type"], "eval_dataset")
            self.assertGreater(manifest["output_counts"]["eval_items"], 0)

    def test_wikidata_can_compile_into_eval_target(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory(prefix="lattice-wikidata-eval-") as tmp:
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
                str(ROOT / "examples" / "targets" / "eval_dataset.yaml"),
                "--fetch-sources-first",
                "--registry",
                str(ROOT / "configs" / "source_registry.json"),
                "--source",
                "wikidata",
                "--compound",
                "lithium iron phosphate",
                "--limit",
                "1",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            manifest = json.loads(result.stdout)
            self.assertGreaterEqual(manifest["fetch"]["counts"].get("wikidata", 0), 1)
            self.assertGreaterEqual(manifest["output_counts"]["eval_items"], 1)


if __name__ == "__main__":
    unittest.main()
