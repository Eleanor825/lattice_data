from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from lattice.targets import load_target_spec, target_spec_from_dict


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

    def test_target_spec_examples_load(self) -> None:
        examples_dir = ROOT / "examples" / "targets"
        for spec_name in (
            "rag_corpus.yaml",
            "pretrain_corpus.yaml",
            "sft_dataset.yaml",
            "preference_dataset.yaml",
            "eval_dataset.yaml",
        ):
            spec = load_target_spec(examples_dir / spec_name)
            self.assertTrue(spec.target_type)
            self.assertEqual(spec.domain, "materials")

    def test_target_spec_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported target_type"):
            target_spec_from_dict({"target_type": "bad_target", "domain": "materials"})

        with self.assertRaisesRegex(ValueError, "field 'domain' is required"):
            target_spec_from_dict({"target_type": "rag_corpus"})

        with self.assertRaisesRegex(ValueError, "Unsupported license_policy"):
            target_spec_from_dict(
                {
                    "target_type": "rag_corpus",
                    "domain": "materials",
                    "license_policy": "bad_policy",
                }
            )

        with self.assertRaisesRegex(ValueError, "target_config.chunk_size"):
            target_spec_from_dict(
                {
                    "target_type": "rag_corpus",
                    "domain": "materials",
                    "target_config": {"chunk_size": 0},
                }
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

    def test_rebuild_from_saved_spec(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-rerun-") as tmp:
            output_dir = Path(tmp) / "out"
            rerun_dir = Path(tmp) / "rerun"
            spec_path = ROOT / "examples" / "targets" / "rag_corpus.yaml"
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
            ]
            first_result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            first_manifest = json.loads(first_result.stdout)

            saved_spec = Path(output_dir) / "reports" / "saved_target_spec.json"
            self.assertTrue(saved_spec.exists())

            rerun_cmd = [
                sys.executable,
                "-m",
                "lattice",
                "build-target",
                "--input",
                str(ROOT / "examples" / "materials" / "raw"),
                "--output",
                str(rerun_dir),
                "--target-spec",
                str(saved_spec),
            ]
            rerun_result = subprocess.run(rerun_cmd, check=True, capture_output=True, text=True, env=self._env())
            rerun_manifest = json.loads(rerun_result.stdout)
            self.assertEqual(first_manifest["target_type"], rerun_manifest["target_type"])
            self.assertEqual(first_manifest["target_spec"]["target_type"], rerun_manifest["target_spec"]["target_type"])

    def test_build_target_can_sync_registry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-target-registry-") as tmp:
            db_path = Path(tmp) / "registry.db"
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
                "--registry-db",
                str(db_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
            from lattice.platform.registry import PlatformRegistry

            registry = PlatformRegistry(db_path)
            try:
                runs = registry.list_runs()
                datasets = registry.list_datasets()
            finally:
                registry.close()
            self.assertTrue(any(run["phase"] == "target" for run in runs))
            self.assertTrue(any(dataset["phase"] == "target" for dataset in datasets))


if __name__ == "__main__":
    unittest.main()
