from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TrainingWorkflowTest(unittest.TestCase):
    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        return env

    def test_training_workflow_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lattice-train-") as tmp:
            pretrain_dir = Path(tmp) / "pretrain"
            continue_dir = Path(tmp) / "continue"
            finetune_dir = Path(tmp) / "finetune"
            post_dir = Path(tmp) / "post"
            data_dir = ROOT / "examples" / "training" / "demo_dataset"

            commands = [
                [
                    sys.executable, "-m", "lattice", "train-pretrain",
                    "--input", str(data_dir),
                    "--output", str(pretrain_dir),
                    "--run-name", "pretrain-demo",
                    "--epochs", "1",
                ],
                [
                    sys.executable, "-m", "lattice", "train-continue",
                    "--input", str(data_dir),
                    "--output", str(continue_dir),
                    "--run-name", "continue-demo",
                    "--checkpoint-dir", str(pretrain_dir),
                    "--epochs", "1",
                ],
                [
                    sys.executable, "-m", "lattice", "train-finetune",
                    "--input", str(data_dir),
                    "--output", str(finetune_dir),
                    "--run-name", "finetune-demo",
                    "--checkpoint-dir", str(continue_dir),
                    "--epochs", "1",
                ],
                [
                    sys.executable, "-m", "lattice", "train-post",
                    "--input", str(data_dir),
                    "--output", str(post_dir),
                    "--run-name", "post-demo",
                    "--checkpoint-dir", str(finetune_dir),
                    "--epochs", "1",
                ],
            ]

            for cmd in commands:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=self._env())
                payload = json.loads(result.stdout)
                self.assertIn("workflow", payload)
                self.assertIn("final_loss", payload)

            manifest = json.loads((post_dir / "reports" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["workflow"], "posttrain")
            self.assertGreater(manifest["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
