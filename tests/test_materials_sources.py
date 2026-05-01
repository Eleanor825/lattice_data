from __future__ import annotations

from socket import timeout as SocketTimeout
import unittest
from urllib.error import URLError

from lattice.sources.materials_project import resolve_materials_project_api_key
from lattice.sources.nomad import fetch_nomad_materials
from lattice.sources.oqmd import fetch_oqmd_structures


class MaterialsSourceTest(unittest.TestCase):
    def test_oqmd_fetch_returns_structured_records(self) -> None:
        try:
            rows = fetch_oqmd_structures(["Li", "O"], limit=1, domain="materials")
        except (TimeoutError, SocketTimeout, URLError) as exc:
            self.skipTest(f"OQMD fetch unavailable during test run: {exc}")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "oqmd")
        self.assertIn("chemical_formula_reduced", rows[0]["payload"]["fields"])
        self.assertIn("band_gap", rows[0]["payload"]["fields"])

    def test_nomad_fetch_returns_structured_records(self) -> None:
        rows = fetch_nomad_materials(["Li", "O"], limit=1, domain="materials")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["schema_type"], "StructuredRecord")
        self.assertEqual(rows[0]["source_type"], "nomad")
        self.assertIn("chemical_formula_reduced", rows[0]["payload"]["fields"])

    def test_materials_project_key_resolution_is_optional(self) -> None:
        value = resolve_materials_project_api_key()
        self.assertTrue(value is None or isinstance(value, str))


if __name__ == "__main__":
    unittest.main()
