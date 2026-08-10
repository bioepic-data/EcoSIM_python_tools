#!/usr/bin/env python3
"""Tests for AmeriFlux ERA5 conversion and in situ validation."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import numpy as np
import pandas as pd

SKILL_DIR = Path(__file__).resolve().parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import era5_to_ecosim_converter as converter


class ConverterComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_inputs(self, shortwave_scale=1.0, measured_shortwave_qc=0):
        timestamps = pd.date_range("2001-06-01", periods=96, freq="30min")
        decimal_hour = timestamps.hour + timestamps.minute / 60.0
        daylight = np.sin(np.pi * (decimal_hour - 5.0) / 15.0)
        shortwave = 850.0 * np.maximum(0.0, daylight)
        temperature = 12.0 + 8.0 * np.sin(2.0 * np.pi * (decimal_hour - 7.0) / 24.0)
        wind = 2.5 + 0.5 * np.sin(2.0 * np.pi * decimal_hour / 24.0)
        vpd_hpa = 8.0 + 2.0 * np.maximum(0.0, daylight)
        pressure = np.full(len(timestamps), 90.0)
        precipitation = np.zeros(len(timestamps))
        precipitation[(timestamps.hour == 3) & (timestamps.minute == 0)] = 0.2

        era = pd.DataFrame(
            {
                "TIMESTAMP_START": timestamps.strftime("%Y%m%d%H%M"),
                "TIMESTAMP_END": (timestamps + pd.Timedelta(minutes=30)).strftime("%Y%m%d%H%M"),
                "TA_ERA": temperature,
                "SW_IN_ERA": shortwave * shortwave_scale,
                "LW_IN_ERA": 300.0,
                "VPD_ERA": vpd_hpa,
                "PA_ERA": pressure,
                "P_ERA": precipitation,
                "WS_ERA": wind,
            }
        )
        fullset = pd.DataFrame(
            {
                "TIMESTAMP_START": timestamps.strftime("%Y%m%d%H%M"),
                "TA_F": temperature,
                "TA_F_QC": 0,
                "SW_IN_F": shortwave,
                "SW_IN_F_QC": measured_shortwave_qc,
                "VPD_F": vpd_hpa,
                "VPD_F_QC": 0,
                "PA_F": pressure,
                "PA_F_QC": 0,
                "P_F": precipitation,
                "P_F_QC": 0,
                "WS_F": wind,
                "WS_F_QC": 0,
            }
        )

        era_file = self.root / "AMF_US-Tst_FLUXNET_ERA5_HH_2001-2001_1-1.csv"
        fullset_file = self.root / "AMF_US-Tst_FLUXNET_FULLSET_HH_2001-2001_1-1.csv"
        era.to_csv(era_file, index=False)
        fullset.to_csv(fullset_file, index=False)
        return era_file, fullset_file

    def convert(self, era_file, output_name="forcing.nc", in_situ_file=None):
        output_file = self.root / output_name
        report_file = self.root / f"{output_name}.quality.json"
        report = converter.convert_era5_to_ecosim(
            str(era_file),
            str(output_file),
            longitude=-121.5,
            quality_report_file=str(report_file),
            in_situ_file=str(in_situ_file) if in_situ_file else None,
            comparison_min_pairs=24,
        )
        return report, json.loads(report_file.read_text())

    def test_auto_discovers_matching_fullset(self):
        era_file, fullset_file = self.write_inputs()
        discovered = converter.discover_in_situ_file(str(era_file), "US-Tst")
        self.assertTrue(os.path.samefile(discovered, fullset_file))

    def test_matching_forcing_passes_without_warnings(self):
        era_file, fullset_file = self.write_inputs()
        report, persisted = self.convert(era_file, in_situ_file=fullset_file)
        comparison = report["in_situ_comparison"]

        self.assertEqual(comparison["status"], "compared")
        self.assertEqual(comparison["warnings"], [])
        self.assertEqual(comparison["variables"]["SRADH"]["paired_hours"], 48)
        self.assertLess(comparison["variables"]["SRADH"]["root_mean_square_error"], 1.0e-4)
        self.assertEqual(persisted["in_situ_comparison"]["status"], "compared")

    def test_large_shortwave_underestimate_emits_warning(self):
        era_file, fullset_file = self.write_inputs(shortwave_scale=0.10)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            report, _ = self.convert(era_file, "low_shortwave.nc", fullset_file)

        comparison = report["in_situ_comparison"]
        warning_variables = {warning["variable"] for warning in comparison["warnings"]}
        self.assertIn("SRADH", warning_variables)
        self.assertIn("WARNING: SRADH", stderr.getvalue())
        self.assertLess(
            comparison["variables"]["SRADH"]["relative_mean_bias_fraction"],
            -0.85,
        )

    def test_qc_two_records_are_not_treated_as_in_situ_measurements(self):
        era_file, fullset_file = self.write_inputs(
            shortwave_scale=0.10,
            measured_shortwave_qc=2,
        )
        report, _ = self.convert(era_file, "qc_filtered.nc", fullset_file)
        shortwave = report["in_situ_comparison"]["variables"]["SRADH"]

        self.assertEqual(shortwave["paired_hours"], 0)
        self.assertNotIn(
            "SRADH",
            {warning["variable"] for warning in report["in_situ_comparison"]["warnings"]},
        )

    def test_missing_fullset_is_reported_without_failing_conversion(self):
        era_file, fullset_file = self.write_inputs()
        os.remove(fullset_file)
        report, _ = self.convert(era_file, "no_observations.nc")

        comparison = report["in_situ_comparison"]
        self.assertEqual(comparison["status"], "not_available")
        self.assertIn("No matching", comparison["reason"])


if __name__ == "__main__":
    unittest.main()
