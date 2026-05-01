from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TargetScoringTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def _build(self, target_spec: str, output_dir: Path) -> list[dict]:
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
            str(ROOT / "examples" / "targets" / target_spec),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
        if target_spec == "rag_corpus.yaml":
            path = output_dir / "outputs" / "chunks.jsonl"
        elif target_spec == "pretrain_corpus.yaml":
            path = output_dir / "outputs" / "pretrain_spans.jsonl"
        else:
            path = output_dir / "outputs" / "instruction_samples.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_target_outputs_include_score_breakdowns(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-scoring-") as tmp:
            rag_rows = self._build("rag_corpus.yaml", Path(tmp) / "rag")
            sft_rows = self._build("sft_dataset.yaml", Path(tmp) / "sft")
            pre_rows = self._build("pretrain_corpus.yaml", Path(tmp) / "pre")

            self.assertIn("retrieval_fitness_breakdown", rag_rows[0])
            self.assertIn("sft_fitness_breakdown", sft_rows[0])
            self.assertIn("pretrain_fitness_breakdown", pre_rows[0])

    def test_different_targets_emit_different_primary_scores(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-score-diff-") as tmp:
            rag_rows = self._build("rag_corpus.yaml", Path(tmp) / "rag")
            pre_rows = self._build("pretrain_corpus.yaml", Path(tmp) / "pre")

            rag_keys = set(rag_rows[0].keys())
            pre_keys = set(pre_rows[0].keys())
            self.assertIn("retrieval_fitness", rag_keys)
            self.assertIn("pretrain_fitness", pre_keys)
            self.assertNotIn("pretrain_fitness", rag_keys)
            self.assertNotIn("retrieval_fitness", pre_keys)


if __name__ == "__main__":
    unittest.main()
