#!/usr/bin/env python3
"""Create Stordalen Mire EcoSIM future climate scenarios from CMIP6 daily anomalies."""

from __future__ import annotations

import argparse
import calendar
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import gcsfs
import intake
import numpy as np
import pandas as pd
import xarray as xr
import zarr


CATALOG_URL = "https://storage.googleapis.com/cmip6/pangeo-cmip6.json"
LAT = 68.35
LON = 19.05
SOURCE_ID = "CanESM5"
MEMBER_ID = "r1i1p1f1"
GRID_LABEL = "gn"
BASELINE_YEARS = (1995, 2014)
FUTURE_YEARS = (2018, 2100)
SCENARIOS = ("ssp245", "ssp585")

CMIP_TO_ECOSIM = {
    "tas": "TMPH",
    "sfcWind": "WINDH",
    "pr": "RAINH",
    "rsds": "SRADH",
}
CMIP_VARIABLE_TABLES = {
    "tas": "day",
    "sfcWind": "day",
    "pr": "day",
    "rsds": "day",
    "huss": "day",
    "ps": "Amon",
}

ADDITIVE_VARS = {"tas", "sfcWind", "rsds"}
RATIO_VARS = {"pr"}
FILL_VALUE = np.float32(1.0e30)
PR_FLOOR_MM_DAY = 0.1
EPSILON = 0.622


@dataclass(frozen=True)
class CmipRecord:
    variable_id: str
    experiment_id: str
    table_id: str
    zstore: str
    version: str
    selected_lat: float | None = None
    selected_lon: float | None = None
    units: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="inputs/FenStordIsland.clim.1960-2017.nc",
        help="Historical EcoSIM climate forcing NetCDF.",
    )
    parser.add_argument(
        "--output-dir",
        default="result/Stordalen_Mire",
        help="Directory for scenario outputs.",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=list(SCENARIOS),
        choices=list(SCENARIOS),
        help="SSP experiments to build.",
    )
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--member-id", default=MEMBER_ID)
    parser.add_argument("--grid-label", default=GRID_LABEL)
    return parser.parse_args()


def is_leap_year(year: int) -> bool:
    return calendar.isleap(year)


def iter_year_dates(year: int):
    for day_idx in range(366 if is_leap_year(year) else 365):
        yield day_idx, date.fromordinal(date(year, 1, 1).toordinal() + day_idx)


def month_day(dt: date) -> str:
    return f"{dt.month:02d}-{dt.day:02d}"


def valid_array(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    arr[~np.isfinite(arr)] = np.nan
    arr[np.abs(arr) > 1.0e20] = np.nan
    return arr


def site_hourly_month_day_climatology(
    ds: xr.Dataset, var_name: str, baseline_years: tuple[int, int]
) -> dict[str, np.ndarray]:
    accum: dict[str, list[np.ndarray]] = defaultdict(list)
    years = ds["year"].values.astype(int)
    baseline_mask = (years >= baseline_years[0]) & (years <= baseline_years[1])

    for year in years[baseline_mask]:
        year_values = valid_array(ds[var_name].sel(year=year).values)
        for day_idx, dt in iter_year_dates(int(year)):
            day_slice = year_values[day_idx, :, :]
            if np.isfinite(day_slice).any():
                accum[month_day(dt)].append(day_slice)

    clim: dict[str, np.ndarray] = {}
    for key, slices in accum.items():
        clim[key] = np.nanmean(np.stack(slices, axis=0), axis=0).astype(np.float32)
    return clim


def year_level_extension(ds: xr.Dataset, var_name: str) -> np.ndarray:
    years = ds["year"].values.astype(int)
    baseline_mask = (years >= BASELINE_YEARS[0]) & (years <= BASELINE_YEARS[1])
    values = valid_array(ds[var_name].values)
    baseline = values[baseline_mask, :]
    if np.isfinite(baseline).any():
        return np.nanmean(baseline, axis=0).astype(np.float32)
    return valid_array(ds[var_name].isel(year=-1).values).astype(np.float32)


def load_catalog_subset(source_id: str, member_id: str, grid_label: str) -> pd.DataFrame:
    cat = intake.open_esm_datastore(CATALOG_URL)
    df = cat.df
    required = list(CMIP_VARIABLE_TABLES)
    experiments = ["historical", *SCENARIOS]
    subset = df[
        (df["source_id"] == source_id)
        & (df["member_id"] == member_id)
        & (df["grid_label"] == grid_label)
        & (df["variable_id"].isin(required))
        & (df["experiment_id"].isin(experiments))
    ].copy()
    if subset.empty:
        raise RuntimeError("No matching daily CMIP6 catalog records were found.")
    return subset


def select_records(
    subset: pd.DataFrame, scenario: str, source_id: str, member_id: str, grid_label: str
) -> dict[tuple[str, str], CmipRecord]:
    records: dict[tuple[str, str], CmipRecord] = {}
    for experiment_id in ("historical", scenario):
        for variable_id, table_id in CMIP_VARIABLE_TABLES.items():
            rows = subset[
                (subset["experiment_id"] == experiment_id)
                & (subset["variable_id"] == variable_id)
                & (subset["table_id"] == table_id)
            ].copy()
            if rows.empty:
                continue
            rows["version_sort"] = rows["version"].astype(str)
            row = rows.sort_values("version_sort").iloc[-1]
            records[(experiment_id, variable_id)] = CmipRecord(
                variable_id=variable_id,
                experiment_id=experiment_id,
                table_id=table_id,
                zstore=row["zstore"],
                version=str(row["version"]),
            )

    missing = [
        f"{experiment_id}:{variable_id}"
        for experiment_id in ("historical", scenario)
        for variable_id in CMIP_VARIABLE_TABLES
        if (experiment_id, variable_id) not in records
    ]
    if missing:
        print(
            "WARNING: missing CMIP6 records; corresponding EcoSIM variables will use "
            f"historical climatology without anomaly: {', '.join(missing)}"
        )
    return records


def open_zarr_dataset(zstore: str, fs: gcsfs.GCSFileSystem) -> xr.Dataset:
    mapper = fs.get_mapper(zstore)
    try:
        return xr.open_zarr(mapper, consolidated=True)
    except Exception:
        return xr.open_zarr(mapper, consolidated=False)


def coord_name(ds: xr.Dataset, candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        if name in ds.coords or name in ds.variables:
            return name
    return None


def select_point(da: xr.DataArray, lat: float, lon: float) -> xr.DataArray:
    lat_name = coord_name(da.to_dataset(name="tmp"), ("lat", "latitude", "nav_lat"))
    lon_name = coord_name(da.to_dataset(name="tmp"), ("lon", "longitude", "nav_lon"))
    if lat_name is None or lon_name is None:
        raise RuntimeError(f"Could not identify lat/lon coordinates for {da.name}.")

    lon_coord = da[lon_name]
    target_lon = lon
    if float(lon_coord.max()) > 180.0 and target_lon < 0.0:
        target_lon = target_lon % 360.0

    if da[lat_name].ndim == 1 and da[lon_name].ndim == 1:
        return da.sel({lat_name: lat, lon_name: target_lon}, method="nearest")

    lon_values = np.asarray(lon_coord)
    lat_values = np.asarray(da[lat_name])
    wrapped = np.abs(((lon_values - target_lon + 180.0) % 360.0) - 180.0)
    distance2 = (lat_values - lat) ** 2 + wrapped**2
    flat_index = int(np.nanargmin(distance2))
    idx = np.unravel_index(flat_index, distance2.shape)
    dims = da[lat_name].dims
    indexers = {dim: i for dim, i in zip(dims, idx)}
    return da.isel(indexers)


def convert_cmip_units(values: np.ndarray, variable_id: str, units: str | None) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    units_norm = (units or "").strip().lower()
    if variable_id == "tas":
        if units_norm in {"k", "kelvin"}:
            arr = arr - 273.15
    elif variable_id == "pr":
        # CMIP precipitation flux is commonly kg m-2 s-1. Since 1 kg m-2 water
        # equals 1 mm water, multiply by seconds per day for daily depth.
        if "s-1" in units_norm or "s**-1" in units_norm or "s^-1" in units_norm:
            arr = arr * 86400.0
    return arr


def cmip_point_series(
    record: CmipRecord,
    fs: gcsfs.GCSFileSystem,
    start: str,
    end: str,
) -> tuple[pd.DataFrame, CmipRecord]:
    mapper = fs.get_mapper(record.zstore)
    ds = open_zarr_dataset(record.zstore, fs)
    da = ds[record.variable_id]
    lat_name = coord_name(da.to_dataset(name="tmp"), ("lat", "latitude", "nav_lat"))
    lon_name = coord_name(da.to_dataset(name="tmp"), ("lon", "longitude", "nav_lon"))
    if lat_name is None or lon_name is None:
        raise RuntimeError(f"Could not identify lat/lon coordinates for {da.name}.")

    target_lon = LON
    lon_coord = da[lon_name]
    if float(lon_coord.max()) > 180.0 and target_lon < 0.0:
        target_lon = target_lon % 360.0

    if da[lat_name].ndim == 1 and da[lon_name].ndim == 1:
        lat_values = np.asarray(da[lat_name].values, dtype=float)
        lon_values = np.asarray(da[lon_name].values, dtype=float)
        ilat = int(np.nanargmin(np.abs(lat_values - LAT)))
        ilon = int(np.nanargmin(np.abs(((lon_values - target_lon + 180.0) % 360.0) - 180.0)))
        selected_lat = float(lat_values[ilat])
        selected_lon = float(lon_values[ilon])
        time_values = da["time"].values
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        selected_indices = []
        times = []
        for idx, item in enumerate(time_values):
            if hasattr(item, "year") and hasattr(item, "month") and hasattr(item, "day"):
                ts = pd.Timestamp(year=int(item.year), month=int(item.month), day=int(item.day))
            else:
                ts = pd.Timestamp(item)
            if start_ts <= ts <= end_ts:
                selected_indices.append(idx)
                times.append(ts)
        if not selected_indices:
            raise RuntimeError(
                f"No time values found for {record.variable_id} {record.experiment_id} in {start}:{end}."
            )
        first = selected_indices[0]
        last = selected_indices[-1]
        zgroup = zarr.open_group(mapper, mode="r")
        values = zgroup[record.variable_id].oindex[first : last + 1, ilat, ilon]
    else:
        da = select_point(da, LAT, LON)
        selected_lat = float(da[lat_name].values)
        selected_lon = float(da[lon_name].values)
        da = da.sel(time=slice(start, end)).load()
        values = da.values
        times = []
        for item in da["time"].values:
            if hasattr(item, "year") and hasattr(item, "month") and hasattr(item, "day"):
                times.append(pd.Timestamp(year=int(item.year), month=int(item.month), day=int(item.day)))
            else:
                times.append(pd.Timestamp(item))

    units = da.attrs.get("units")
    values = convert_cmip_units(values, record.variable_id, units)
    normalized_times = []
    for item in times:
        if hasattr(item, "year") and hasattr(item, "month") and hasattr(item, "day"):
            normalized_times.append(pd.Timestamp(year=int(item.year), month=int(item.month), day=int(item.day)))
        else:
            normalized_times.append(pd.Timestamp(item))
    times = pd.DatetimeIndex(normalized_times)
    frame = pd.DataFrame(
        {
            "time": times,
            "month_day": times.strftime("%m-%d"),
            "value": values,
        }
    )
    frame = frame[np.isfinite(frame["value"])]
    updated = CmipRecord(
        variable_id=record.variable_id,
        experiment_id=record.experiment_id,
        table_id=record.table_id,
        zstore=record.zstore,
        version=record.version,
        selected_lat=selected_lat,
        selected_lon=selected_lon,
        units=units,
    )
    return frame, updated


def fill_missing_feb29(values_by_date: dict[date, float], dt: date) -> float:
    if dt.month == 2 and dt.day == 29:
        before = values_by_date.get(date(dt.year, 2, 28))
        after = values_by_date.get(date(dt.year, 3, 1))
        if before is not None and after is not None:
            return float((before + after) / 2.0)
        if before is not None:
            return float(before)
        if after is not None:
            return float(after)
    return np.nan


def derive_vapor_pressure_kpa(huss: pd.DataFrame, ps: pd.DataFrame) -> pd.DataFrame:
    """Derive daily vapor pressure from daily huss and monthly ps."""
    ps_monthly = ps.copy()
    ps_monthly["year_month"] = ps_monthly["time"].dt.to_period("M")
    pressure_by_month = ps_monthly.groupby("year_month")["value"].mean()

    out = huss.copy()
    out["year_month"] = out["time"].dt.to_period("M")
    out["ps_pa"] = out["year_month"].map(pressure_by_month).astype(float)
    q = out["value"].astype(float)
    p = out["ps_pa"].astype(float)
    out["e_kpa"] = (q * p / (EPSILON + (1.0 - EPSILON) * q)) / 1000.0
    return out[np.isfinite(out["e_kpa"])][["time", "month_day", "e_kpa"]]


def cmip_daily_anomalies(
    records: dict[tuple[str, str], CmipRecord],
    scenario: str,
    hist_cache: dict[str, tuple[pd.DataFrame, CmipRecord]],
) -> tuple[pd.DataFrame, list[CmipRecord]]:
    fs = gcsfs.GCSFileSystem(token="anon")
    anomaly_frames = []
    used_records: list[CmipRecord] = []

    for variable_id in CMIP_TO_ECOSIM:
        hist_record = records.get(("historical", variable_id))
        fut_record = records.get((scenario, variable_id))
        if hist_record is None or fut_record is None:
            continue

        if variable_id in hist_cache:
            hist, hist_record = hist_cache[variable_id]
        else:
            print(f"Reading historical {variable_id} point series...", flush=True)
            hist, hist_record = cmip_point_series(hist_record, fs, "1995-01-01", "2014-12-31")
            hist_cache[variable_id] = (hist, hist_record)
        print(f"Reading {scenario} {variable_id} point series...", flush=True)
        fut, fut_record = cmip_point_series(fut_record, fs, "2018-01-01", "2100-12-31")
        used_records.extend([hist_record, fut_record])

        hist_clim = hist.groupby("month_day")["value"].mean()
        fut = fut.copy()
        if variable_id in ADDITIVE_VARS:
            fut["anomaly"] = fut["value"] - fut["month_day"].map(hist_clim)
            col = f"{variable_id}_delta"
        elif variable_id in RATIO_VARS:
            denom = fut["month_day"].map(hist_clim).astype(float)
            denom = denom.where(denom >= PR_FLOOR_MM_DAY, PR_FLOOR_MM_DAY)
            fut["anomaly"] = fut["value"] / denom
            col = f"{variable_id}_ratio"
        else:
            continue

        anomaly_frames.append(
            fut[["time", "month_day", "anomaly"]]
            .rename(columns={"anomaly": col})
            .assign(variable_id=variable_id)
        )

    vapor_keys = [
        ("historical", "huss"),
        ("historical", "ps"),
        (scenario, "huss"),
        (scenario, "ps"),
    ]
    if all(key in records for key in vapor_keys):
        if "huss" in hist_cache:
            hist_huss, hist_huss_record = hist_cache["huss"]
        else:
            print("Reading historical huss point series...", flush=True)
            hist_huss, hist_huss_record = cmip_point_series(
                records[("historical", "huss")], fs, "1995-01-01", "2014-12-31"
            )
            hist_cache["huss"] = (hist_huss, hist_huss_record)

        if "ps" in hist_cache:
            hist_ps, hist_ps_record = hist_cache["ps"]
        else:
            print("Reading historical ps point series...", flush=True)
            hist_ps, hist_ps_record = cmip_point_series(
                records[("historical", "ps")], fs, "1995-01-01", "2014-12-31"
            )
            hist_cache["ps"] = (hist_ps, hist_ps_record)

        print(f"Reading {scenario} huss point series...", flush=True)
        fut_huss, fut_huss_record = cmip_point_series(
            records[(scenario, "huss")], fs, "2018-01-01", "2100-12-31"
        )
        print(f"Reading {scenario} ps point series...", flush=True)
        fut_ps, fut_ps_record = cmip_point_series(
            records[(scenario, "ps")], fs, "2018-01-01", "2100-12-31"
        )
        used_records.extend([hist_huss_record, hist_ps_record, fut_huss_record, fut_ps_record])

        hist_e = derive_vapor_pressure_kpa(hist_huss, hist_ps)
        fut_e = derive_vapor_pressure_kpa(fut_huss, fut_ps)
        hist_e_clim = hist_e.groupby("month_day")["e_kpa"].mean()
        fut_e = fut_e.copy()
        fut_e["e_delta"] = fut_e["e_kpa"] - fut_e["month_day"].map(hist_e_clim)
        anomaly_frames.append(fut_e[["time", "month_day", "e_delta"]].assign(variable_id="e"))
    else:
        missing = [f"{experiment}:{var}" for experiment, var in vapor_keys if (experiment, var) not in records]
        print(
            "WARNING: missing huss/ps records for vapor pressure; DWPTH will use "
            f"historical climatology without anomaly: {', '.join(missing)}",
            flush=True,
        )

    if not anomaly_frames:
        return pd.DataFrame(), used_records

    daily = anomaly_frames[0][["time", "month_day"]].drop_duplicates().copy()
    for frame in anomaly_frames:
        col = [c for c in frame.columns if c.endswith("_delta") or c.endswith("_ratio")][0]
        daily = daily.merge(frame[["time", col]], on="time", how="left")
    return daily.sort_values("time").reset_index(drop=True), used_records


def daily_lookup(anomalies: pd.DataFrame) -> dict[str, dict[date, float]]:
    out: dict[str, dict[date, float]] = {}
    for col in anomalies.columns:
        if not (col.endswith("_delta") or col.endswith("_ratio")):
            continue
        lookup: dict[date, float] = {}
        for row in anomalies[["time", col]].itertuples(index=False):
            if pd.notna(row[1]):
                lookup[row[0].date()] = float(row[1])
        out[col] = lookup
    return out


def build_extended_dataset(
    ds: xr.Dataset,
    scenario: str,
    anomalies: pd.DataFrame,
    records: list[CmipRecord],
) -> xr.Dataset:
    original_years = ds["year"].values.astype(int)
    all_years = np.arange(int(original_years.min()), FUTURE_YEARS[1] + 1, dtype=np.int32)
    future_years = np.arange(int(original_years.max()) + 1, FUTURE_YEARS[1] + 1, dtype=np.int32)
    new = xr.Dataset(coords={"year": all_years})
    lookup = daily_lookup(anomalies)
    source_by_ecosim = {ecosim: "historical_climatology_no_anomaly" for ecosim in ds.data_vars}

    for var_name in ds.data_vars:
        dims = ds[var_name].dims
        attrs = dict(ds[var_name].attrs)
        if dims == ("year", "day", "hour", "ngrid"):
            shape = (len(all_years), ds.sizes["day"], ds.sizes["hour"], ds.sizes["ngrid"])
            data = np.full(shape, np.nan, dtype=np.float32)
            data[: len(original_years), :, :, :] = valid_array(ds[var_name].values).astype(np.float32)
            clim = site_hourly_month_day_climatology(ds, var_name, BASELINE_YEARS)

            for yi, year in enumerate(future_years, start=len(original_years)):
                for day_idx, dt in iter_year_dates(int(year)):
                    md = month_day(dt)
                    base = clim.get(md)
                    if base is None:
                        continue
                    values = base.astype(np.float64)
                    if var_name == "TMPH" and "tas_delta" in lookup:
                        delta = lookup["tas_delta"].get(dt, fill_missing_feb29(lookup["tas_delta"], dt))
                        if np.isfinite(delta):
                            values = values + delta
                            source_by_ecosim[var_name] = "CMIP6_tas_daily_additive_delta"
                    elif var_name == "WINDH" and "sfcWind_delta" in lookup:
                        delta = lookup["sfcWind_delta"].get(
                            dt, fill_missing_feb29(lookup["sfcWind_delta"], dt)
                        )
                        if np.isfinite(delta):
                            values = np.maximum(values + delta, 0.0)
                            source_by_ecosim[var_name] = "CMIP6_sfcWind_daily_additive_delta"
                    elif var_name == "RAINH" and "pr_ratio" in lookup:
                        ratio = lookup["pr_ratio"].get(dt, fill_missing_feb29(lookup["pr_ratio"], dt))
                        if np.isfinite(ratio):
                            values = np.maximum(values * ratio, 0.0)
                            source_by_ecosim[var_name] = "CMIP6_pr_daily_multiplicative_ratio"
                    elif var_name == "SRADH" and "rsds_delta" in lookup:
                        delta = lookup["rsds_delta"].get(dt, fill_missing_feb29(lookup["rsds_delta"], dt))
                        if np.isfinite(delta):
                            values = np.maximum(values + delta, 0.0)
                            source_by_ecosim[var_name] = "CMIP6_rsds_daily_additive_delta"
                    elif var_name == "DWPTH" and "e_delta" in lookup:
                        delta = lookup["e_delta"].get(dt, fill_missing_feb29(lookup["e_delta"], dt))
                        if np.isfinite(delta):
                            values = np.maximum(values + delta, 0.0)
                            source_by_ecosim[var_name] = (
                                "CMIP6_huss_day_ps_Amon_derived_vapor_pressure_daily_additive_delta"
                            )
                    data[yi, day_idx, :, :] = values.astype(np.float32)

            new[var_name] = (dims, data, attrs)
        elif dims == ("year", "ngrid"):
            shape = (len(all_years), ds.sizes["ngrid"])
            data = np.full(shape, np.nan, dtype=np.float32)
            data[: len(original_years), :] = valid_array(ds[var_name].values).astype(np.float32)
            data[len(original_years) :, :] = year_level_extension(ds, var_name)
            new[var_name] = (dims, data, attrs)
        else:
            new[var_name] = ds[var_name]

    selected_records = [
        {
            "variable_id": r.variable_id,
            "experiment_id": r.experiment_id,
            "table_id": r.table_id,
            "zstore": r.zstore,
            "version": r.version,
            "selected_lat": r.selected_lat,
            "selected_lon": r.selected_lon,
            "source_units": r.units,
        }
        for r in records
    ]
    new.attrs.update(
        {
            "title": f"Stordalen Mire EcoSIM climate forcing extended with CMIP6 daily anomalies ({scenario})",
            "source_file": "inputs/FenStordIsland.clim.1960-2017.nc",
            "site_name": "Stordalen Mire",
            "site_latitude": LAT,
            "site_longitude": LON,
            "cmip6_catalog": CATALOG_URL,
            "cmip6_source_id": SOURCE_ID,
            "cmip6_member_id": MEMBER_ID,
            "cmip6_grid_label": GRID_LABEL,
            "cmip6_scenario": scenario,
            "historical_baseline_years": f"{BASELINE_YEARS[0]}-{BASELINE_YEARS[1]}",
            "future_years": f"{FUTURE_YEARS[0]}-{FUTURE_YEARS[1]}",
            "daily_anomaly_policy": (
                "Daily CMIP6 anomalies are applied uniformly to all 24 hourly values "
                "for a calendar day. DWPTH uses an additive vapor-pressure anomaly "
                "derived from daily huss and monthly ps from the same CMIP6 ensemble."
            ),
            "variable_extension_sources": json.dumps(source_by_ecosim, sort_keys=True),
            "cmip6_records": json.dumps(selected_records, sort_keys=True),
            "precipitation_ratio_floor_mm_day": PR_FLOOR_MM_DAY,
        }
    )
    return new


def write_dataset(ds: xr.Dataset, path: Path) -> None:
    encoding = {}
    for name in ds.data_vars:
        if np.issubdtype(ds[name].dtype, np.floating):
            encoding[name] = {"_FillValue": FILL_VALUE, "dtype": "float32"}
    ds.to_netcdf(path, encoding=encoding, unlimited_dims=["year"])


def summarize(ds: xr.Dataset, scenario: str) -> pd.DataFrame:
    rows = []
    baseline = ds.sel(year=slice(BASELINE_YEARS[0], BASELINE_YEARS[1]))
    windows = {
        "2050s": (2041, 2070),
        "2090s": (2071, 2100),
    }
    for var_name in ("TMPH", "WINDH", "RAINH", "DWPTH", "SRADH"):
        base_mean = float(np.nanmean(valid_array(baseline[var_name].values)))
        for label, years in windows.items():
            window = ds.sel(year=slice(years[0], years[1]))
            fut_mean = float(np.nanmean(valid_array(window[var_name].values)))
            row = {
                "scenario": scenario,
                "window": label,
                "years": f"{years[0]}-{years[1]}",
                "variable": var_name,
                "baseline_mean": base_mean,
                "future_mean": fut_mean,
                "delta": fut_mean - base_mean,
                "units": ds[var_name].attrs.get("units", ""),
            }
            if var_name == "RAINH" and base_mean > 0:
                row["ratio"] = fut_mean / base_mean
                row["percent_change"] = (row["ratio"] - 1.0) * 100.0
            else:
                row["ratio"] = np.nan
                row["percent_change"] = np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_id = args.source_id
    member_id = args.member_id
    grid_label = args.grid_label
    global SOURCE_ID, MEMBER_ID, GRID_LABEL
    SOURCE_ID, MEMBER_ID, GRID_LABEL = source_id, member_id, grid_label

    ds = xr.open_dataset(input_path, decode_times=False)
    subset = load_catalog_subset(source_id, member_id, grid_label)
    summaries = []
    hist_cache: dict[str, tuple[pd.DataFrame, CmipRecord]] = {}
    manifest = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "site": {"name": "Stordalen Mire", "lat": LAT, "lon": LON},
        "cmip6": {
            "catalog": CATALOG_URL,
            "source_id": source_id,
            "member_id": member_id,
            "grid_label": grid_label,
            "table_ids": {"daily_variables": "day", "surface_pressure": "Amon"},
        },
        "scenarios": {},
    }

    for scenario in args.scenarios:
        print(f"Building {scenario}...")
        records = select_records(subset, scenario, source_id, member_id, grid_label)
        anomalies, used_records = cmip_daily_anomalies(records, scenario, hist_cache)
        if not anomalies.empty:
            anomaly_path = output_dir / f"Stordalen_Mire_{scenario}_daily_anomalies_2018-2100.csv"
            anomalies.to_csv(anomaly_path, index=False)
        else:
            anomaly_path = None

        extended = build_extended_dataset(ds, scenario, anomalies, used_records)
        output_path = output_dir / f"FenStordIsland.clim.{scenario}.daily_anomaly.1960-2100.nc"
        write_dataset(extended, output_path)

        summary = summarize(extended, scenario)
        summaries.append(summary)
        scenario_manifest = {
            "netcdf": str(output_path),
            "daily_anomalies_csv": str(anomaly_path) if anomaly_path else None,
            "records": json.loads(extended.attrs["cmip6_records"]),
            "variable_extension_sources": json.loads(extended.attrs["variable_extension_sources"]),
        }
        manifest["scenarios"][scenario] = scenario_manifest
        print(f"Wrote {output_path}")

    summary_all = pd.concat(summaries, ignore_index=True)
    summary_path = output_dir / "Stordalen_Mire_daily_anomaly_summary_2050s_2090s.csv"
    summary_all.to_csv(summary_path, index=False)
    manifest["summary_csv"] = str(summary_path)
    manifest_path = output_dir / "Stordalen_Mire_daily_anomaly_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"Wrote {summary_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
