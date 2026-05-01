from __future__ import annotations

import unittest

from lattice.sources.crossref import fetch_crossref_documents
from lattice.sources.europe_pmc import fetch_europe_pmc_documents
from lattice.sources.jarvis import fetch_jarvis_structures
from lattice.sources.materials_cloud_archive import fetch_materials_cloud_records
from lattice.sources.webdocs import fetch_page_document
from lattice.sources.wikidata import fetch_wikidata_knowledge


class AdditionalSourceTest(unittest.TestCase):
    def test_crossref_fetch_returns_documents(self) -> None:
        rows = fetch_crossref_documents("solid state battery electrolyte", limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "crossref")

    def test_openalex_fetch_returns_documents(self) -> None:
        from lattice.sources.openalex import fetch_openalex_documents

        rows = fetch_openalex_documents("solid state battery electrolyte", limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "openalex")
        self.assertTrue(rows[0]["payload"]["title"])
        self.assertTrue(rows[0]["payload"]["text"])

    def test_wikidata_fetch_returns_knowledge(self) -> None:
        rows = fetch_wikidata_knowledge(["lithium iron phosphate"], limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "KnowledgeRecord")
        self.assertEqual(rows[0]["source_type"], "wikidata")

    def test_pubchem_fetch_returns_structured_record(self) -> None:
        from lattice.sources.pubchem import fetch_pubchem_compounds

        rows, warnings = fetch_pubchem_compounds(["lithium iron phosphate"], domain="materials")
        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "pubchem")
        self.assertIn("molecular_formula", rows[0]["payload"]["fields"])

    def test_jarvis_fetch_returns_structured_records(self) -> None:
        rows = fetch_jarvis_structures(["Li", "O"], limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "jarvis")

    def test_europe_pmc_fetch_returns_documents(self) -> None:
        rows = fetch_europe_pmc_documents("solid state battery electrolyte", limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "europe_pmc")
        self.assertGreaterEqual(len(rows[0]["payload"]["text"].split()), 10)

    def test_arxiv_fetch_returns_documents(self) -> None:
        from lattice.sources.arxiv import fetch_arxiv_documents

        rows = fetch_arxiv_documents("solid state battery electrolyte", limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "arxiv")
        self.assertTrue(rows[0]["payload"]["title"])
        self.assertTrue(rows[0]["payload"]["text"])

    def test_materials_cloud_fetch_returns_documents(self) -> None:
        rows = fetch_materials_cloud_records("solid state battery", limit=1, domain="materials")
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "materials_cloud_archive")

    def test_webdoc_fetch_returns_document(self) -> None:
        rows = fetch_page_document(
            "battery_archive",
            "https://batteryarchive.org/",
            domain="materials",
            note="Battery Archive landing page.",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "Document")
        self.assertEqual(rows[0]["source_type"], "battery_archive")


if __name__ == "__main__":
    unittest.main()
