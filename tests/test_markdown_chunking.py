from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from lattice.ingest.text_adapter import parse_text_file


ROOT = Path(__file__).resolve().parents[1]


class MarkdownChunkingTest(unittest.TestCase):
    def test_text_ingest_extracts_markdown_sections(self) -> None:
        records = parse_text_file(ROOT / "examples" / "materials" / "raw" / "papers" / "solid_state_batteries.txt", "materials")
        self.assertEqual(len(records), 1)
        sections = records[0].payload["sections"]
        self.assertIsInstance(sections, list)

    def test_rag_chunks_preserve_section_field(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory(prefix="lattice-md-rag-") as tmp:
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
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            rows = [
                json.loads(line)
                for line in (output_dir / "outputs" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(rows)
            self.assertTrue(all("section" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
