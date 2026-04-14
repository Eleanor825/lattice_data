from __future__ import annotations

import unittest

from lattice.sources.crossref import fetch_crossref_documents
from lattice.sources.jarvis import fetch_jarvis_structures
from lattice.sources.wikidata import fetch_wikidata_knowledge


class AdditionalSourceTest(unittest.TestCase):
    def test_crossref_fetch_returns_documents(self) -> None:
        rows = fetch_crossref_documents("solid state battery electrolyte", limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "crossref")

    def test_wikidata_fetch_returns_knowledge(self) -> None:
        rows = fetch_wikidata_knowledge(["lithium iron phosphate"], limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "KnowledgeRecord")
        self.assertEqual(rows[0]["source_type"], "wikidata")

    def test_jarvis_fetch_returns_structured_records(self) -> None:
        rows = fetch_jarvis_structures(["Li", "O"], limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "jarvis")


if __name__ == "__main__":
    unittest.main()
