from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PreferenceTargetTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_preference_target_outputs_pairs_with_reasons(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-pref-target-") as tmp:
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
                str(ROOT / "examples" / "targets" / "preference_dataset.yaml"),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            rows = [
                json.loads(line)
                for line in (output_dir / "outputs" / "preference_pairs.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertGreater(len(rows), 0)
            for row in rows:
                self.assertIn("chosen", row)
                self.assertIn("rejected", row)
                self.assertIn("reason_code", row)
                self.assertIn("pair_validity", row)
                self.assertGreaterEqual(float(row["pair_validity"]), 1.0)
                self.assertTrue(row["source_record_id"])
            self.assertEqual(manifest["target_type"], "preference_dataset")
            self.assertGreater(manifest["output_counts"]["preference_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
