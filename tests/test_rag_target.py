from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RagTargetTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_rag_target_outputs_grounded_chunks_with_citations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-rag-target-") as tmp:
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
                str(ROOT / "examples" / "targets" / "rag_corpus.yaml"),
                "--source",
                "openalex",
                "--source",
                "pubchem",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            chunks_path = output_dir / "outputs" / "chunks.jsonl"
            self.assertTrue(chunks_path.exists())
            rows = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertGreater(len(rows), 0)
            for row in rows:
                self.assertIn("citation_payload", row)
                self.assertTrue(row["citation_payload"]["source_ref"])
                self.assertTrue(row["citation_payload"]["source_type"])
                self.assertIn("retrieval_fitness", row)
                self.assertIn("citation_completeness", row)
                self.assertGreaterEqual(float(row["citation_completeness"]), 1.0)
                self.assertIn("entity_ids", row)
            self.assertEqual(manifest["target_type"], "rag_corpus")
            self.assertGreater(manifest["output_counts"]["chunks"], 0)


if __name__ == "__main__":
    unittest.main()
