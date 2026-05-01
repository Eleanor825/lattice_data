from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TargetBuildTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def _write_spec(self, path: Path, target_type: str) -> None:
        path.write_text(
            "\n".join(
                [
                    f"target_type: {target_type}",
                    "domain: materials",
                    "consumer: test",
                    "license_policy: research_only",
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

    def test_build_target_rag(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-rag-") as tmp:
            spec_path = Path(tmp) / "rag.yaml"
            output_dir = Path(tmp) / "out"
            self._write_spec(spec_path, "rag_corpus")
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
                str(spec_path),
                "--source",
                "openalex",
                "--source",
                "pubchem",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            manifest = json.loads(result.stdout)
            self.assertEqual(manifest["target_type"], "rag_corpus")
            self.assertTrue((output_dir / "outputs" / "chunks.jsonl").exists())
            self.assertTrue((output_dir / "outputs" / "entities.jsonl").exists())
            self.assertTrue((output_dir / "outputs" / "links.jsonl").exists())
            self.assertTrue((output_dir / "reports" / "manifest.json").exists())
            self.assertTrue((output_dir / "reports" / "dataset_card.md").exists())
            self.assertGreater(manifest["output_counts"]["chunks"], 0)

    def test_build_target_sft_and_eval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-sft-") as tmp:
            sft_spec = Path(tmp) / "sft.yaml"
            eval_spec = Path(tmp) / "eval.yaml"
            sft_out = Path(tmp) / "sft"
            eval_out = Path(tmp) / "eval"
            self._write_spec(sft_spec, "sft_dataset")
            self._write_spec(eval_spec, "eval_dataset")

            sft_cmd = [
                sys.executable,
                "-m",
                "lattice",
                "build-target",
                "--input",
                str(ROOT / "examples" / "materials" / "raw"),
                "--output",
                str(sft_out),
                "--target-spec",
                str(sft_spec),
            ]
            eval_cmd = [
                sys.executable,
                "-m",
                "lattice",
                "build-target",
                "--input",
                str(ROOT / "examples" / "materials" / "raw"),
                "--output",
                str(eval_out),
                "--target-spec",
                str(eval_spec),
            ]

            sft_result = subprocess.run(sft_cmd, check=True, capture_output=True, text=True, env=self._env())
            eval_result = subprocess.run(eval_cmd, check=True, capture_output=True, text=True, env=self._env())
            sft_manifest = json.loads(sft_result.stdout)
            eval_manifest = json.loads(eval_result.stdout)
            self.assertEqual(sft_manifest["target_type"], "sft_dataset")
            self.assertEqual(eval_manifest["target_type"], "eval_dataset")
            self.assertTrue((sft_out / "outputs" / "instruction_samples.jsonl").exists())
            self.assertTrue((eval_out / "outputs" / "eval_items.jsonl").exists())
            self.assertGreater(sft_manifest["output_counts"]["instruction_samples"], 0)
            self.assertGreater(eval_manifest["output_counts"]["eval_items"], 0)


if __name__ == "__main__":
    unittest.main()
