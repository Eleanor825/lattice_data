from __future__ import annotations

import unittest

from lattice.targets.artifacts import Artifact
from lattice.targets.specs import target_spec_from_dict
from lattice.targets.transforms import Transform, register_default_transforms, register_transform


def _dummy_summary_transform(inputs: list[Artifact], _spec) -> list[Artifact]:
    rows: list[Artifact] = []
    for artifact in inputs:
        if artifact.artifact_type != "Document":
            continue
        rows.append(
            Artifact(
                artifact_id=f"dummy-{artifact.artifact_id}",
                artifact_type="DummySummary",
                domain=artifact.domain,
                payload={"summary": str(artifact.payload.get("text", ""))[:40]},
                source_refs=list(artifact.source_refs),
                license_status=artifact.license_status,
                quality={},
                policy=dict(artifact.policy),
                lineage=list(artifact.lineage),
            )
        )
    return rows


class TransformExtensionTest(unittest.TestCase):
    def test_custom_transform_can_be_registered(self) -> None:
        registry = register_default_transforms()
        register_transform(
            registry,
            Transform(
                name="document_to_dummy_summary",
                input_types=("Document",),
                output_type="DummySummary",
                supported_targets={"rag_corpus"},
                runner=_dummy_summary_transform,
            ),
        )
        self.assertIn("document_to_dummy_summary", registry)

    def test_custom_transform_runs_on_artifacts(self) -> None:
        registry = register_default_transforms()
        register_transform(
            registry,
            Transform(
                name="document_to_dummy_summary",
                input_types=("Document",),
                output_type="DummySummary",
                supported_targets={"rag_corpus"},
                runner=_dummy_summary_transform,
            ),
        )
        spec = target_spec_from_dict({"target_type": "rag_corpus", "domain": "materials"})
        artifact = Artifact(
            artifact_id="doc-1",
            artifact_type="Document",
            domain="materials",
            payload={"title": "Doc", "text": "This is a short materials document for testing."},
            source_refs=[{"source_id": "demo", "source_type": "text", "source_ref": "demo.txt"}],
            lineage=["doc-1"],
        )
        rows = registry["document_to_dummy_summary"].run([artifact], spec)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].artifact_type, "DummySummary")
        self.assertIn("summary", rows[0].payload)


if __name__ == "__main__":
    unittest.main()
