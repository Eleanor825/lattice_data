from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PretrainTargetTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_pretrain_target_outputs_spans_with_scores(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-pretrain-target-") as tmp:
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
                str(ROOT / "examples" / "targets" / "pretrain_corpus.yaml"),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            rows = [
                json.loads(line)
                for line in (output_dir / "outputs" / "pretrain_spans.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertGreater(len(rows), 0)
            for row in rows:
                self.assertIn("text", row)
                self.assertIn("pretrain_fitness", row)
                self.assertIn("source_balance_hint", row)
                self.assertTrue(row["source_record_id"])
            self.assertEqual(manifest["target_type"], "pretrain_corpus")
            self.assertGreater(manifest["output_counts"]["pretrain_spans"], 0)


if __name__ == "__main__":
    unittest.main()
