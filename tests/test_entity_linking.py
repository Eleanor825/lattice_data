from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from lattice.compiler.quality import filter_records
from lattice.ingest import ingest_directory
from lattice.targets.fusion import build_entity_bundles
from lattice.targets.transforms import build_base_artifacts, register_default_transforms
from lattice.targets.specs import load_target_spec


ROOT = Path(__file__).resolve().parents[1]


class EntityLinkingTest(unittest.TestCase):
    def test_entity_bundles_collect_evidence_and_conflicts(self) -> None:
        records, _warnings = ingest_directory(ROOT / "examples" / "materials" / "raw", domain="materials")
        kept_records, _dropped = filter_records(records)
        base_artifacts = build_base_artifacts(kept_records)
        transforms = register_default_transforms()
        spec = load_target_spec(ROOT / "examples" / "targets" / "rag_corpus.yaml")
        entity_artifacts = transforms["record_to_entity"].run(base_artifacts, spec)
        bundles = build_entity_bundles(base_artifacts, entity_artifacts)
        self.assertGreater(len(bundles), 0)
        self.assertTrue(any(bundle.evidence for bundle in bundles))
        self.assertTrue(any(bundle.properties for bundle in bundles))

    def test_manifest_reports_entity_bundle_counts(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory(prefix="lattice-entity-linking-") as tmp:
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
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            manifest = json.loads(result.stdout)
            self.assertIn("entity_bundle_count", manifest)
            self.assertIn("entity_conflict_count", manifest)
            self.assertGreaterEqual(manifest["entity_bundle_count"], 1)


if __name__ == "__main__":
    unittest.main()
