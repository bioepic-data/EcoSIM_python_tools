from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "select_gapon_template.py"
SPEC = importlib.util.spec_from_file_location("select_gapon_template", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SelectGaponTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = MODULE.load_catalog()

    def test_catalog_profiles_are_complete_and_readable(self) -> None:
        self.assertEqual(len(self.catalog), 24)
        for template in self.catalog:
            profile = MODULE.load_profile(template)
            self.assertGreater(len(profile), 0)
            for row in profile:
                for column in MODULE.COEFFICIENT_COLUMNS:
                    self.assertGreaterEqual(float(row[column]), 0.0)

    def select(self, water: str, management: str) -> dict[str, str]:
        template, _ = MODULE.choose_template(
            self.catalog,
            None,
            "maize soybean cropland",
            "warm temperate",
            "maize soybean crop rotation",
            water,
            management,
        )
        return template

    def test_dryland_and_irrigated_crop_templates_are_distinguished(self) -> None:
        self.assertEqual(
            self.select("dry", "dryland rotation")["template_id"],
            "warm_temperate_maize_soybean_dryland_ne",
        )
        self.assertEqual(
            self.select("irrigated", "irrigated rotation")["template_id"],
            "warm_temperate_maize_soybean_irrigated_ne",
        )

    def test_arctic_wetland_selects_same_ecosystem_family(self) -> None:
        template, _ = MODULE.choose_template(
            self.catalog, None, "wetland", "arctic", "wetland", "wet", "natural"
        )
        self.assertEqual(template["template_id"], "arctic_wetland_nwt_dlmtsoil")

    def test_depth_mapping_uses_containing_layer_and_deepest_extension(self) -> None:
        template = next(
            row for row in self.catalog
            if row["template_id"] == "cool_temperate_douglas_fir_bc"
        )
        profile = MODULE.load_profile(template)
        target_depths = [0.01, 0.05, 0.20, 3.0]
        mapped = MODULE.depth_map_profile(profile, target_depths)
        source_depths = [float(item["source"]["layer_bottom_depth_m"]) for item in mapped]
        all_source_depths = [float(row["layer_bottom_depth_m"]) for row in profile]
        self.assertEqual([item["layer_bottom_depth_m"] for item in mapped], target_depths)
        self.assertGreaterEqual(source_depths[0], target_depths[0])
        self.assertGreaterEqual(source_depths[1], target_depths[1])
        self.assertGreaterEqual(source_depths[2], target_depths[2])
        self.assertEqual(source_depths[3], all_source_depths[-1])
        self.assertFalse(mapped[2]["depth_extended"])
        self.assertTrue(mapped[3]["depth_extended"])

    def test_cli_writes_template_warning_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "gapon.csv"
            status = MODULE.main(
                [
                    "--ecosystem-type", "maize soybean cropland",
                    "--climate", "warm temperate",
                    "--water-regime", "dry",
                    "--management", "dryland rotation",
                    "--target-depths", "0.1,0.5,1.0",
                    "--output", str(output),
                ]
            )
            self.assertEqual(status, 0)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            provenance = json.loads(output.with_suffix(".provenance.json").read_text())
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(row["qc_flags"] == "template_based;subject_to_tuning" for row in rows))
            self.assertTrue(provenance["template_based"])
            self.assertTrue(provenance["subject_to_tuning"])
            self.assertEqual(provenance["notice"], MODULE.NOTICE)


if __name__ == "__main__":
    unittest.main()
