#!/usr/bin/env python3
"""Build EcoSIM atmospheric GHG NetCDF files from historical atmgas and SSP paths."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset


RCMIP_URL = (
    "https://rcmip-protocols-au.s3-ap-southeast-2.amazonaws.com/"
    "v5.1.0/rcmip-concentrations-annual-means-v5-1-0.csv"
)

RCMIP_VARIABLES = {
    "CO2": ("Atmospheric Concentrations|CO2", "ppmv"),
    "CH4": ("Atmospheric Concentrations|CH4", "ppbv"),
    "N2O": ("Atmospheric Concentrations|N2O", "ppbv"),
}

LONG_NAMES = {
    "CO2": "Atmospheric CO2 concentration",
    "CH4": "Atmospheric CH4 concentrations",
    "N2O": "Atmospheric N2O concentration",
}

SCENARIO_LABELS = {
    "ssp119": "SSP1-1.9",
    "ssp126": "SSP1-2.6",
    "ssp245": "SSP2-4.5",
    "ssp370": "SSP3-7.0",
    "ssp434": "SSP4-3.4",
    "ssp460": "SSP4-6.0",
    "ssp534-over": "SSP5-3.4-OS",
    "ssp585": "SSP5-8.5",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--historical-netcdf",
        required=True,
        help="EcoSIM historical atmgas NetCDF containing year, CO2, CH4, and N2O.",
    )
    parser.add_argument(
        "--rcmip-csv",
        help="Local RCMIP concentrations annual means CSV. Required unless --download-rcmip is set.",
    )
    parser.add_argument(
        "--download-rcmip",
        action="store_true",
        help="Download the default RCMIP CSV into the output directory when --rcmip-csv is omitted.",
    )
    parser.add_argument(
        "--output-dir",
        default="result/ssp_gas_concentrations",
        help="Directory for NetCDF and CSV outputs.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["ssp245", "ssp585"],
        help="RCMIP SSP scenario IDs to write.",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1750,
        help="First calendar year to include from the historical file.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2100,
        help="Last calendar year to include from RCMIP SSP pathways.",
    )
    parser.add_argument(
        "--splice-year",
        type=int,
        help=(
            "First calendar year to take from the SSP pathway. "
            "Default: first year after the last complete historical calendar year."
        ),
    )
    parser.add_argument(
        "--key-years",
        nargs="+",
        type=int,
        default=[2015, 2020, 2030, 2050, 2070, 2100],
        help="Calendar years to include in the summary CSV.",
    )
    return parser.parse_args()


def download_rcmip_csv(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "rcmip-concentrations-annual-means-v5-1-0.csv"
    try:
        urllib.request.urlretrieve(RCMIP_URL, dest)
    except Exception as exc:
        raise RuntimeError(
            "Could not download RCMIP CSV. Download it separately with an approved "
            "network command and pass --rcmip-csv."
        ) from exc
    return dest


def month_calendar_year(fractional_years: np.ndarray) -> np.ndarray:
    """Map EcoSIM fractional years to calendar years.

    EcoSIM atmgas files produced by atmgasWriter use year + month / 12, with
    December represented by the following integer year. A tiny epsilon avoids
    floating-point edge cases around integer December coordinates.
    """

    return np.floor(fractional_years - 1.0e-5).astype(int)


def read_historical(path: Path, start_year: int) -> dict[str, np.ndarray]:
    with Dataset(path) as ds:
        required = ["year", "CO2", "CH4", "N2O"]
        missing = [name for name in required if name not in ds.variables]
        if missing:
            raise ValueError(f"Historical NetCDF is missing variables: {', '.join(missing)}")

        years = np.asarray(ds.variables["year"][:], dtype=np.float64)
        cal_years = month_calendar_year(years)
        mask = cal_years >= start_year
        if not mask.any():
            raise ValueError(f"No historical records found at or after {start_year}.")

        data: dict[str, np.ndarray] = {"year": years[mask]}
        for gas in RCMIP_VARIABLES:
            data[gas] = np.asarray(ds.variables[gas][:], dtype=np.float64)[mask]
        return data


def last_complete_calendar_year(years: np.ndarray) -> int:
    cal_years = month_calendar_year(years)
    complete = []
    for year in np.unique(cal_years):
        if np.count_nonzero(cal_years == year) == 12:
            complete.append(int(year))
    if not complete:
        raise ValueError("Historical NetCDF does not contain any complete calendar year.")
    return max(complete)


def read_rcmip(path: Path, scenarios: list[str], end_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(path)
    year_columns = [col for col in df.columns if col.isdigit()]
    if str(end_year) not in year_columns:
        raise ValueError(f"RCMIP CSV does not include requested end year {end_year}.")

    selected_rows = []
    annual_records = []
    for scenario in scenarios:
        for gas, (variable, unit) in RCMIP_VARIABLES.items():
            rows = df[
                (df["Scenario"] == scenario)
                & (df["Region"] == "World")
                & (df["Variable"] == variable)
            ]
            if rows.empty:
                raise ValueError(f"Missing RCMIP row for {scenario} {variable} World.")
            row = rows.iloc[0]
            selected_rows.append(
                {
                    "scenario": scenario,
                    "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
                    "source_model": row["Model"],
                    "gas": gas,
                    "unit": unit,
                    "rcmip_variable": variable,
                }
            )
            for year in year_columns:
                year_int = int(year)
                if year_int <= end_year:
                    annual_records.append(
                        {
                            "scenario": scenario,
                            "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
                            "source_model": row["Model"],
                            "gas": gas,
                            "unit": unit,
                            "year": year_int,
                            "concentration": float(row[year]),
                        }
                    )
    metadata = pd.DataFrame(selected_rows)
    annual = pd.DataFrame(annual_records)
    return metadata, annual


def future_months_from_annual(
    annual: pd.DataFrame, scenario: str, start_year: int, end_year: int
) -> dict[str, np.ndarray]:
    years = []
    gases = {gas: [] for gas in RCMIP_VARIABLES}
    for year in range(start_year, end_year + 1):
        years.extend(year + np.arange(1, 13, dtype=np.float64) / 12.0)
        for gas in RCMIP_VARIABLES:
            match = annual[
                (annual["scenario"] == scenario)
                & (annual["gas"] == gas)
                & (annual["year"] == year)
            ]
            if match.empty:
                raise ValueError(f"Missing annual RCMIP value for {scenario} {gas} {year}.")
            gases[gas].extend([float(match.iloc[0]["concentration"])] * 12)
    out: dict[str, np.ndarray] = {"year": np.asarray(years, dtype=np.float64)}
    for gas, values in gases.items():
        out[gas] = np.asarray(values, dtype=np.float64)
    return out


def write_scenario_netcdf(
    output_path: Path,
    historical: dict[str, np.ndarray],
    future: dict[str, np.ndarray],
    scenario: str,
    scenario_metadata: pd.DataFrame,
    historical_path: Path,
    rcmip_path: Path,
    splice_year: int,
    end_year: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    years = np.concatenate([historical["year"], future["year"]])

    with Dataset(output_path, "w") as ds:
        ds.createDimension("time", None)
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        models = ", ".join(
            f"{row.gas}:{row.source_model}" for row in scenario_metadata.itertuples()
        )
        ds.description = (
            f"EcoSIM atmospheric CO2, CH4, and N2O concentration forcing for {scenario}; "
            f"historical monthly data spliced with RCMIP annual SSP concentrations; "
            f"created {now}"
        )
        ds.source_historical = str(historical_path)
        ds.source_rcmip = str(rcmip_path)
        ds.rcmip_url = RCMIP_URL
        ds.scenario = scenario
        ds.scenario_label = SCENARIO_LABELS.get(scenario, scenario)
        ds.rcmip_source_models = models
        ds.splice_calendar_year = splice_year
        ds.end_calendar_year = end_year
        ds.future_monthly_policy = (
            "annual_step: every month of each future calendar year is assigned "
            "that year's RCMIP annual mean concentration"
        )
        ds.fractional_year_note = (
            "EcoSIM convention: month coordinate is calendar_year + month/12; "
            "December is represented by the following integer year."
        )

        year_var = ds.createVariable("year", "f4", ("time",))
        year_var.long_name = "Year AD"
        year_var[:] = years.astype(np.float32)

        for gas, (_, units) in RCMIP_VARIABLES.items():
            var = ds.createVariable(gas, "f4", ("time",))
            var.long_name = LONG_NAMES[gas]
            var.units = units
            var[:] = np.concatenate([historical[gas], future[gas]]).astype(np.float32)


def main() -> int:
    args = parse_args()
    historical_path = Path(args.historical_netcdf).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if args.rcmip_csv:
        rcmip_path = Path(args.rcmip_csv).expanduser().resolve()
    elif args.download_rcmip:
        rcmip_path = download_rcmip_csv(output_dir)
    else:
        raise SystemExit("Pass --rcmip-csv or use --download-rcmip.")

    historical_all = read_historical(historical_path, args.start_year)
    hist_last_complete = last_complete_calendar_year(historical_all["year"])
    splice_year = args.splice_year or (hist_last_complete + 1)
    if splice_year > args.end_year:
        raise ValueError("--splice-year cannot be later than --end-year.")

    hist_cal = month_calendar_year(historical_all["year"])
    historical = {
        name: values[hist_cal < splice_year]
        for name, values in historical_all.items()
    }

    metadata, annual = read_rcmip(rcmip_path, args.scenarios, args.end_year)
    outputs = []
    for scenario in args.scenarios:
        future = future_months_from_annual(annual, scenario, splice_year, args.end_year)
        scenario_meta = metadata[metadata["scenario"] == scenario]
        out_path = output_dir / f"fatm_GHGs_{scenario}_{args.start_year}-{args.end_year}.nc"
        write_scenario_netcdf(
            out_path,
            historical,
            future,
            scenario,
            scenario_meta,
            historical_path,
            rcmip_path,
            splice_year,
            args.end_year,
        )
        outputs.append(out_path)

    annual_out = output_dir / "ssp_atmgas_annual_rcmip_values.csv"
    key_out = output_dir / "ssp_atmgas_key_years.csv"
    annual[
        annual["scenario"].isin(args.scenarios)
        & annual["year"].between(args.start_year, args.end_year)
    ].to_csv(annual_out, index=False)
    annual[
        annual["scenario"].isin(args.scenarios)
        & annual["year"].isin(args.key_years)
    ].to_csv(key_out, index=False)

    print("Wrote NetCDF files:")
    for path in outputs:
        print(f"  {path}")
    print("Wrote CSV summaries:")
    print(f"  {annual_out}")
    print(f"  {key_out}")
    print(f"Historical complete through calendar year: {hist_last_complete}")
    print(f"SSP splice starts at calendar year: {splice_year}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
