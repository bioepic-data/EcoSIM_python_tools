#!/usr/bin/env python3

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_plant_trait_desc.py"
SPEC = importlib.util.spec_from_file_location("trait_checker", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def parameter(variable, value, line, raw_value=None):
    return CHECKER.Parameter(
        index=line,
        variable=variable,
        description="test",
        raw_value=str(value) if raw_value is None else raw_value,
        numeric_values=[float(value)],
        section="PHOTOSYNTHETIC PROPERTIES",
        line=line,
    )


def c4_block(values):
    block = CHECKER.PlantBlock(nz=1, ny=1, nx=1, code="maiz41", start_line=1)
    block.parameters = [parameter("ICTYP", 1, 1, "C4 1.0")]
    block.parameters.extend(
        parameter(variable, value, line)
        for line, (variable, value) in enumerate(values.items(), start=2)
    )
    return block


def c3_block(values):
    block = CHECKER.PlantBlock(nz=1, ny=1, nx=1, code="soyb41", start_line=1)
    block.parameters = [parameter("ICTYP", 1, 1, "C3 0.0")]
    block.parameters.extend(
        parameter(variable, value, line)
        for line, (variable, value) in enumerate(values.items(), start=2)
    )
    return block


def physiology_findings(block):
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

    CHECKER.check_physiological_parameterization(block, CHECKER.by_var(block), add)
    return findings


class PhysiologicalParameterizationTests(unittest.TestCase):
    def test_missing_pathway_is_flagged_instead_of_skipped(self):
        block = CHECKER.PlantBlock(nz=1, ny=1, nx=1, code="test00", start_line=1)
        findings = physiology_findings(block)
        self.assertEqual([finding.parameter for finding in findings], ["ICTYP"])
        self.assertEqual(findings[0].category, "physiology")

    def test_compensating_maize_parameters_are_flagged(self):
        block = c4_block(
            {
                "VCMX": 45,
                "VOMX": 12,
                "XKCO2": 30,
                "XKO2": 810,
                "RUBP": 0.10,
                "ETMX": 1400,
                "VCMX4": 400,
                "XKCO24": 3,
                "PEPC": 0.12,
                "CHL": 0.20,
                "fCHLMESO": 0.60,
                "FCO2": 0.40,
                "CNWL": 2.7,
                "ALBR": 0.20,
                "TAUR": 0.20,
                "ALBP": 0.075,
                "TAUP": 0.075,
            }
        )
        flagged = {finding.parameter for finding in physiology_findings(block)}
        self.assertEqual(
            flagged,
            {
                "XKO2",
                "VCMX/VOMX",
                "PEPC/CNWL",
                "VCMX4*PEPC/VCMX*RUBP",
                "ETMX*CHL/VCMX*RUBP",
            },
        )

    def test_balanced_c4_parameterization_passes(self):
        block = c4_block(
            {
                "VCMX": 100,
                "VOMX": 12,
                "XKCO2": 16,
                "XKO2": 183,
                "RUBP": 0.065,
                "ETMX": 1000,
                "VCMX4": 150,
                "XKCO24": 3,
                "PEPC": 0.04,
                "CHL": 0.20,
                "fCHLMESO": 0.60,
                "FCO2": 0.35,
                "CNWL": 2.7,
                "ALBR": 0.20,
                "TAUR": 0.20,
                "ALBP": 0.09,
                "TAUP": 0.04,
            }
        )
        self.assertEqual(physiology_findings(block), [])

    def test_float32_boundary_values_are_accepted(self):
        block = c3_block(
            {
                "VCMX": 60,
                "VOMX": 30,
                "XKCO2": 10,
                "XKO2": 500,
                "RUBP": 0.34999999403953552,
                "ETMX": 550,
                "CHL": 0.30000001192092896,
                "FCO2": 0.70,
                "CNWL": 2.8,
                "ALBR": 0.20,
                "TAUR": 0.20,
                "ALBP": 0.075,
                "TAUP": 0.075,
            }
        )
        self.assertEqual(physiology_findings(block), [])
        self.assertTrue(CHECKER.in_range(0.30000001192092896, (0.08, 0.30)))

    def test_strict_mode_only_promotes_physiology_warnings(self):
        findings = [
            CHECKER.Finding("WARN", "maiz41", 1, 1, 1, 2, "XKO2", "high", "physiology"),
            CHECKER.Finding("WARN", "maiz41", 1, 1, 1, 3, "RRAD2M", "large", "general"),
        ]
        promoted = CHECKER.enforce_strict_physiology(findings)
        severities = {finding.parameter: finding.severity for finding in promoted}
        self.assertEqual(severities, {"XKO2": "ERROR", "RRAD2M": "WARN"})


if __name__ == "__main__":
    unittest.main()
