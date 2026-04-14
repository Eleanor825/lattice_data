from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PipelineTest(unittest.TestCase):
    def test_compile_pipeline_end_to_end(self) -> None:
        output_dir = Path(tempfile.mkdtemp(prefix="lattice-test-"))
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        cmd = [
            sys.executable,
            "-m",
            "lattice",
            "compile",
            "--input",
            str(ROOT / "examples" / "materials" / "raw"),
            "--output",
            str(output_dir),
            "--domain",
            "materials",
            "--dataset-name",
            "Lattice-Materials-Test",
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        manifest = json.loads(result.stdout)

        self.assertEqual(manifest["dataset_name"], "Lattice-Materials-Test")
        self.assertGreaterEqual(manifest["kept_record_count"], 3)
        self.assertGreaterEqual(manifest["view_counts"]["pretrain_view"], 2)
        self.assertGreaterEqual(manifest["view_counts"]["knowledge_view"], 2)
        self.assertIn("source_counts", manifest)
        self.assertGreaterEqual(manifest["dropped_records"].get("duplicate", 0), 1)
        self.assertGreaterEqual(manifest["dropped_records"].get("boilerplate", 0), 1)

        normalized_path = output_dir / "normalized" / "records.jsonl"
        first_record = json.loads(normalized_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertIn("provenance_chain", first_record["metadata"])
        self.assertIn("dedup_id", first_record["metadata"])
        self.assertIn("timestamp", first_record["metadata"])
        self.assertTrue((output_dir / "reports" / "dataset_card.md").exists())
        self.assertTrue((output_dir / "reports" / "source_coverage.json").exists())


if __name__ == "__main__":
    unittest.main()
