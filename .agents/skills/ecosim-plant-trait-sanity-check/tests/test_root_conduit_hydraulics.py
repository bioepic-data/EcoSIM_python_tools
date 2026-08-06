#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_plant_trait_desc.py"
SPEC = importlib.util.spec_from_file_location("trait_checker_root_hydraulics", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def parameter(variable, value, line):
    return CHECKER.Parameter(
        index=line,
        variable=variable,
        description="test",
        raw_value=str(value),
        numeric_values=[float(value)],
        section="ROOT CHARACTERISTICS",
        line=line,
    )


def hydraulic_findings(code, values, include_default_rsrr=True):
    values = dict(values)
    if include_default_rsrr:
        values.setdefault("RSRR", 5000.0)
    block = CHECKER.PlantBlock(nz=1, ny=1, nx=1, code=code, start_line=1)
    block.parameters = [
        parameter(variable, value, line)
        for line, (variable, value) in enumerate(values.items(), start=1)
    ]
    findings = []

    def add(block, severity, parameter, line, message, category="general"):
        findings.append(
            CHECKER.Finding(
                severity=severity,
                pft_code=block.code,
                nz=block.nz,
                ny=block.ny,
                nx=block.nx,
                line=line,
                parameter=parameter,
                message=message,
                category=category,
            )
        )

    params = CHECKER.by_var(block)
    CHECKER.check_variable_ranges(block, params, add)
    CHECKER.check_root_radial_hydraulics(block, params, add)
    CHECKER.check_root_conduit_hydraulics(block, params, add)
    return findings


class RootConduitHydraulicsTests(unittest.TestCase):
    def test_plant_summary_always_reports_rsrr_conversion(self):
        block = CHECKER.PlantBlock(nz=1, ny=1, nx=1, code="ndlf35", start_line=1)
        block.parameters = [parameter("RSRR", 5000.0, 1)]
        summary = CHECKER.block_summary(block, [])
        self.assertEqual(summary["rsrr_mpa_h_per_m"], 5000.0)
        self.assertAlmostEqual(summary["root_radial_conductivity_m_per_s_mpa"], 5.555555555555556e-8)

    def test_defensible_conifer_rsrr_passes(self):
        findings = hydraulic_findings(
            "ndlf35",
            {"RSRR": 5000.0, "RRAD2M": 2.5e-4, "RVSR": 15.2e-6, "ARSRA": 2.0},
        )
        self.assertEqual(findings, [])

    def test_high_conifer_rsrr_reports_implied_conductivity(self):
        findings = hydraulic_findings(
            "ndlf35",
            {"RSRR": 27777.78, "RRAD2M": 2.5e-4, "RVSR": 15.2e-6, "ARSRA": 2.0},
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].parameter, "RSRR")
        self.assertEqual(findings[0].category, "hydraulics")
        self.assertIn("1e-08 m s-1 MPa-1", findings[0].message)
        self.assertIn("micropores dry", findings[0].message)

    def test_missing_rsrr_is_an_error(self):
        findings = hydraulic_findings(
            "ndlf35",
            {"RRAD2M": 2.5e-4, "RVSR": 15.2e-6, "ARSRA": 2.0},
            include_default_rsrr=False,
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(findings[0].parameter, "RSRR")

    def test_nonconifer_rsrr_outside_broad_conductivity_screen_warns(self):
        findings = hydraulic_findings(
            "maiz41",
            {"RSRR": 100000.0, "RRAD2M": 2.5e-4, "RVSR": 10.0e-6, "ARSRA": 2.0},
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].parameter, "RSRR")
        self.assertEqual(findings[0].severity, "WARN")

    def test_ponderosa_root_conduit_radius_passes(self):
        findings = hydraulic_findings(
            "ndlf35",
            {"RRAD2M": 2.5e-4, "RVSR": 15.2e-6, "ARSRA": 2.0},
        )
        self.assertEqual(findings, [])

    def test_small_conifer_radius_is_flagged_as_literal_anatomy(self):
        findings = hydraulic_findings(
            "ndlf35",
            {"RRAD2M": 2.5e-4, "RVSR": 1.413889e-6, "ARSRA": 2.0},
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].parameter, "RVSR")
        self.assertEqual(findings[0].category, "hydraulics")
        self.assertIn("diameter", findings[0].message)
        self.assertIn("use ARSRA", findings[0].message)

    def test_impossible_conduit_count_is_an_error(self):
        findings = hydraulic_findings(
            "maiz41",
            {"RRAD2M": 1.0e-4, "RVSR": 6.0e-5, "ARSRA": 2.0},
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(findings[0].parameter, "RVSR/RRAD2M")
        self.assertIn("expected at least one conduit", findings[0].message)

    def test_arsra_below_one_is_flagged(self):
        findings = hydraulic_findings(
            "maiz41",
            {"RRAD2M": 2.5e-4, "RVSR": 10.0e-6, "ARSRA": 0.8},
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].parameter, "ARSRA")
        self.assertEqual(findings[0].category, "hydraulics")
        self.assertIn("expected ARSRA >= 1", findings[0].message)

    def test_missing_rvsr_is_an_error(self):
        findings = hydraulic_findings("ndlf35", {"RRAD2M": 2.5e-4, "ARSRA": 2.0})
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(findings[0].parameter, "RVSR")

    def test_missing_arsra_is_an_error(self):
        findings = hydraulic_findings("ndlf35", {"RRAD2M": 2.5e-4, "RVSR": 15.2e-6})
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(findings[0].parameter, "ARSRA")


if __name__ == "__main__":
    unittest.main()
