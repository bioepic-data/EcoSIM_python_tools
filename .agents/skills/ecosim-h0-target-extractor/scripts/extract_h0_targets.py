#!/usr/bin/env python3
"""Extract typical annual and mid-season targets from EcoSIM h0 NetCDF output."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    from netCDF4 import Dataset, num2date
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("ERROR: this extractor requires the netCDF4 Python package.") from exc


DEFAULT_VARS = {
    "gpp": "ECO_GPP_col",
    "et": "ECO_ET_col",
    "lai": "ECO_LAI_col",
    "root_biomass": "Root_C_pft",
    "shoot_biomass": "SHOOT_C_pft",
    "canopy_height": "CAN_HT_pft",
    "primary_root_depth": "Root1stDepz_pft",
    "vcmax25": "VcMax25C_RUBISCO_pft",
    "jmax25": "JMax25C_photo_pft",
    "sla": "SLA_pft",
}


def jsonable(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def attrs_for(var) -> Dict[str, object]:
    return {name: jsonable(getattr(var, name)) for name in var.ncattrs()}


def parse_date(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def parse_mmdd(text: str) -> Tuple[int, int]:
    match = re.fullmatch(r"(\d{2})-(\d{2})", text)
    if not match:
        raise argparse.ArgumentTypeError(f"Expected MM-DD, got {text!r}")
    month = int(match.group(1))
    day = int(match.group(2))
    try:
        date(2001, month, day)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return month, day


def infer_start_date_from_name(path: Path) -> Optional[date]:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def first_datetime_to_date(value) -> date:
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return date(int(value.year), int(value.month), int(value.day))
    return parse_date(str(value)[:10])


def decode_dates(ds: Dataset, path: Path, start_date: Optional[date]) -> Tuple[List[date], str, List[str]]:
    warnings: List[str] = []
    if "time" not in ds.dimensions:
        raise ValueError("No time dimension found in h0 file.")
    ntime = len(ds.dimensions["time"])

    if "time" in ds.variables and hasattr(ds.variables["time"], "units"):
        time_var = ds.variables["time"]
        calendar = getattr(time_var, "calendar", "standard")
        decoded = num2date(time_var[:], units=time_var.units, calendar=calendar)
        return [first_datetime_to_date(x) for x in decoded], f"time units: {time_var.units}", warnings

    if "time_bounds" in ds.variables and hasattr(ds.variables["time_bounds"], "units"):
        tb = ds.variables["time_bounds"]
        calendar = getattr(tb, "calendar", "standard")
        decoded = num2date(tb[:, 0], units=tb.units, calendar=calendar)
        return [first_datetime_to_date(x) for x in decoded], f"time_bounds units: {tb.units}", warnings

    inferred = start_date or infer_start_date_from_name(path)
    if inferred is None:
        raise ValueError(
            "No dated time coordinate found and no YYYY-MM-DD pattern in filename. "
            "Pass --start-date YYYY-MM-DD."
        )
    warnings.append(
        "No time-coordinate units found; dates were inferred as daily steps from "
        f"{inferred.isoformat()}."
    )
    return [inferred + timedelta(days=i) for i in range(ntime)], "daily dates inferred from start date", warnings


def as_float_array(var) -> np.ndarray:
    data = np.ma.filled(var[:], np.nan).astype(float)
    for attr in ("_FillValue", "missing_value"):
        if hasattr(var, attr):
            fill = float(getattr(var, attr))
            data[np.isclose(data, fill)] = np.nan
    data[np.abs(data) > 1.0e29] = np.nan
    return data


def move_time_first(data: np.ndarray, dims: Sequence[str]) -> np.ndarray:
    if "time" not in dims:
        raise ValueError(f"Variable has no time dimension: {dims}")
    return np.moveaxis(data, dims.index("time"), 0)


def nanmean_flat_non_time(data: np.ndarray, dims: Sequence[str]) -> np.ndarray:
    arr = move_time_first(data, dims)
    if arr.ndim == 1:
        return arr
    with np.errstate(all="ignore"):
        return np.nanmean(arr.reshape(arr.shape[0], -1), axis=1)


def nansum_preserve_nan(data: np.ndarray, axis: int) -> np.ndarray:
    finite = np.isfinite(data)
    summed = np.nansum(data, axis=axis)
    summed = np.asarray(summed, dtype=float)
    all_nan = ~np.any(finite, axis=axis)
    summed[all_nan] = np.nan
    return summed


def nanmax_preserve_nan(data: np.ndarray, axis: int) -> np.ndarray:
    finite = np.isfinite(data)
    maxed = np.max(np.where(finite, data, -np.inf), axis=axis)
    maxed = np.asarray(maxed, dtype=float)
    all_nan = ~np.any(finite, axis=axis)
    maxed[all_nan] = np.nan
    return maxed


def pft_sum_series(data: np.ndarray, dims: Sequence[str]) -> np.ndarray:
    arr = move_time_first(data, dims)
    non_time_dims = list(dims)
    non_time_dims.pop(dims.index("time"))
    if "pft" in non_time_dims:
        arr = nansum_preserve_nan(arr, axis=1 + non_time_dims.index("pft"))
    if arr.ndim == 1:
        return arr
    with np.errstate(all="ignore"):
        return np.nanmean(arr.reshape(arr.shape[0], -1), axis=1)


def max_flat_non_time_series(data: np.ndarray, dims: Sequence[str]) -> np.ndarray:
    arr = move_time_first(data, dims)
    if arr.ndim == 1:
        return arr
    return nanmax_preserve_nan(arr.reshape(arr.shape[0], -1), axis=1)


def active_pft_mean_series(data: np.ndarray, dims: Sequence[str]) -> np.ndarray:
    arr = move_time_first(data, dims)
    if arr.ndim == 1:
        return arr
    with np.errstate(all="ignore"):
        return np.nanmean(arr.reshape(arr.shape[0], -1), axis=1)


def build_capacity_weights(ds: Dataset, args: argparse.Namespace) -> Tuple[Optional[np.ndarray], Optional[Sequence[str]], str, List[str]]:
    warnings: List[str] = []

    if args.capacity_weight_method == "active_pft_mean":
        return None, None, "active_pft_mean", warnings

    if args.capacity_weight_method == "variable":
        if not args.capacity_weight_var:
            raise ValueError("--capacity-weight-var is required when --capacity-weight-method variable.")
        if args.capacity_weight_var not in ds.variables:
            raise ValueError(f"Capacity weight variable not found: {args.capacity_weight_var}")
        if args.capacity_weight_var == "LAIstk_pft":
            warnings.append("LAIstk_pft includes stalk area; using it only because it was explicitly requested.")
        var = ds.variables[args.capacity_weight_var]
        return as_float_array(var), var.dimensions, f"weighted_by_{args.capacity_weight_var}", warnings

    if args.capacity_weight_method in {"auto", "shoot_sla_proxy"}:
        if args.shoot_var in ds.variables and args.sla_var in ds.variables:
            shoot = ds.variables[args.shoot_var]
            sla = ds.variables[args.sla_var]
            shoot_data = as_float_array(shoot)
            sla_data = as_float_array(sla)
            if shoot.dimensions == sla.dimensions and shoot_data.shape == sla_data.shape:
                # SLA is cm2 leaf per gC leaf. The 1e-4 factor converts cm2 to m2.
                proxy = shoot_data * sla_data * 1.0e-4
                proxy[proxy <= 0.0] = np.nan
                warnings.append(
                    f"Vcmax/Jmax were weighted by {args.shoot_var} * {args.sla_var} * 1e-4 "
                    "as a PFT leaf-area proxy. This avoids LAIstk_pft, which includes stalk area, "
                    "but remains approximate because shoot C can include non-leaf shoot tissue."
                )
                return proxy, shoot.dimensions, "weighted_by_shoot_c_sla_leaf_area_proxy", warnings
            warnings.append(
                f"{args.shoot_var} and {args.sla_var} shapes or dimensions differ; "
                "using active-PFT mean for Vcmax/Jmax."
            )
        else:
            warnings.append(
                f"{args.shoot_var} or {args.sla_var} not found; using active-PFT mean for Vcmax/Jmax."
            )
        return None, None, "active_pft_mean", warnings

    raise ValueError(f"Unknown capacity weight method: {args.capacity_weight_method}")


def weighted_pft_series(
    data: np.ndarray,
    dims: Sequence[str],
    weights: Optional[np.ndarray],
    weight_dims: Optional[Sequence[str]],
) -> Tuple[np.ndarray, bool]:
    if weights is None or weight_dims is None:
        return active_pft_mean_series(data, dims), False

    arr = move_time_first(data, dims)
    w = move_time_first(weights, weight_dims)
    if arr.shape != w.shape:
        return active_pft_mean_series(data, dims), False

    finite = np.isfinite(arr) & np.isfinite(w) & (w > 0.0)
    num = np.nansum(np.where(finite, arr * w, np.nan), axis=1)
    den = np.nansum(np.where(finite, w, np.nan), axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        weighted = num / den
    fallback = active_pft_mean_series(data, dims)
    bad = ~np.isfinite(weighted)
    weighted[bad] = fallback[bad]
    if weighted.ndim == 1:
        return weighted, True
    with np.errstate(all="ignore"):
        return np.nanmean(weighted.reshape(weighted.shape[0], -1), axis=1), True


def complete_year_indices(dates: Sequence[date]) -> Tuple[Dict[int, np.ndarray], List[str]]:
    warnings: List[str] = []
    grouped: Dict[int, List[int]] = {}
    for idx, dt in enumerate(dates):
        grouped.setdefault(dt.year, []).append(idx)

    complete: Dict[int, np.ndarray] = {}
    for year, indices in sorted(grouped.items()):
        year_dates = {dates[idx] for idx in indices}
        if date(year, 1, 1) in year_dates and date(year, 12, 31) in year_dates:
            complete[year] = np.array(indices, dtype=int)
    if not complete:
        warnings.append("No complete calendar years found; using all available years.")
        complete = {year: np.array(indices, dtype=int) for year, indices in sorted(grouped.items())}
    return complete, warnings


def finite_last(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    return float(finite[-1]) if finite.size else math.nan


def finite_first(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    return float(finite[0]) if finite.size else math.nan


def infer_annual_method(name: str, attrs: Dict[str, object], requested: str) -> str:
    if requested != "auto":
        return requested
    text = " ".join(str(attrs.get(key, "")) for key in ("long_name", "cell_method", "units"))
    if "cumulative" in f"{name} {text}".lower() or "cum" in name.lower():
        return "year_end_cumulative"
    return "sum_interval"


def annual_values(series: np.ndarray, years: Dict[int, np.ndarray], method: str) -> Tuple[List[Dict[str, object]], List[str]]:
    rows: List[Dict[str, object]] = []
    warnings: List[str] = []
    for year, idx in years.items():
        vals = series[idx]
        finite = vals[np.isfinite(vals)]
        first = finite_first(vals)
        peak = float(np.nanmax(vals)) if finite.size else math.nan
        if method == "year_end_cumulative":
            value = finite_last(vals)
            if np.isfinite(peak) and np.isfinite(value) and peak - value > max(1.0e-6, abs(peak) * 0.01):
                warnings.append(
                    f"{year}: cumulative peak ({peak:.6g}) exceeds year-end value ({value:.6g}); "
                    "reported year-end net cumulative value."
                )
        elif method == "max_cumulative":
            value = peak
        elif method == "diff_cumulative":
            last = finite_last(vals)
            value = float(last - first) if np.isfinite(first) and np.isfinite(last) else math.nan
        elif method == "sum_interval":
            value = float(np.nansum(vals)) if finite.size else math.nan
        else:
            raise ValueError(f"Unknown annual method: {method}")
        rows.append(
            {
                "year": int(year),
                "value": value,
                "n_time_steps": int(len(idx)),
                "first_value": first,
                "max_value": peak,
            }
        )
    return rows, warnings


def annual_state_values(series: np.ndarray, years: Dict[int, np.ndarray], stat: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for year, idx in years.items():
        vals = series[idx]
        finite = vals[np.isfinite(vals)]
        if finite.size == 0:
            value = math.nan
        elif stat == "max":
            value = float(np.nanmax(finite))
        elif stat == "mean":
            value = float(np.nanmean(finite))
        elif stat == "median":
            value = float(np.nanmedian(finite))
        else:
            raise ValueError(f"Unknown annual state statistic: {stat}")
        rows.append({"year": int(year), "value": value, "n_time_steps": int(len(idx))})
    return rows


def in_midseason(dt: date, start_md: Tuple[int, int], end_md: Tuple[int, int]) -> bool:
    md = (dt.month, dt.day)
    if start_md <= end_md:
        return start_md <= md <= end_md
    return md >= start_md or md <= end_md


def midseason_values(
    series: np.ndarray,
    dates: Sequence[date],
    years: Dict[int, np.ndarray],
    start_md: Tuple[int, int],
    end_md: Tuple[int, int],
    stat: str,
) -> List[Dict[str, object]]:
    date_array = np.array(dates, dtype=object)
    rows: List[Dict[str, object]] = []
    for year, idx in years.items():
        season_idx = np.array([i for i in idx if in_midseason(date_array[i], start_md, end_md)], dtype=int)
        vals = series[season_idx]
        if vals.size == 0 or not np.any(np.isfinite(vals)):
            value = math.nan
        elif stat == "mean":
            value = float(np.nanmean(vals))
        else:
            value = float(np.nanmedian(vals))
        rows.append({"year": int(year), "value": value, "n_time_steps": int(season_idx.size)})
    return rows


def summarize(values: Sequence[Dict[str, object]], statistic: str) -> Dict[str, object]:
    arr = np.array([float(item["value"]) for item in values], dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {
            "typical_statistic": statistic,
            "typical_value": math.nan,
            "mean": math.nan,
            "std": math.nan,
            "min": math.nan,
            "max": math.nan,
            "n_years": 0,
        }
    if statistic == "mean":
        typical = float(np.nanmean(finite))
    elif statistic == "max":
        typical = float(np.nanmax(finite))
    else:
        typical = float(np.nanmedian(finite))
    return {
        "typical_statistic": statistic,
        "typical_value": typical,
        "mean": float(np.nanmean(finite)),
        "std": float(np.nanstd(finite, ddof=1)) if finite.size > 1 else 0.0,
        "min": float(np.nanmin(finite)),
        "max": float(np.nanmax(finite)),
        "n_years": int(finite.size),
    }


def require_variable(ds: Dataset, name: str, label: str) -> None:
    if name not in ds.variables:
        raise ValueError(f"Required variable for {label} not found: {name}")


def metric_record(
    label: str,
    variable: str,
    units: str,
    temporal_context: str,
    method: str,
    values: List[Dict[str, object]],
    summary_stat: str,
    source_attrs: Dict[str, object],
    warnings: Optional[List[str]] = None,
    weight_note: Optional[str] = None,
) -> Dict[str, object]:
    record: Dict[str, object] = {
        "label": label,
        "variable": variable,
        "units": units,
        "temporal_context": temporal_context,
        "method": method,
        "summary": summarize(values, summary_stat),
        "year_values": values,
        "source_attrs": source_attrs,
    }
    if warnings:
        record["warnings"] = warnings
    if weight_note:
        record["weight_note"] = weight_note
    return record


def collect_target_units(metrics: Dict[str, object]) -> Dict[str, Dict[str, str]]:
    return {
        key: {
            "variable": str(metric["variable"]),
            "units": str(metric["units"]),
            "temporal_context": str(metric["temporal_context"]),
        }
        for key, metric in metrics.items()
    }


def collect_target_ranges(metrics: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    ranges: Dict[str, Dict[str, object]] = {}
    for key, metric in metrics.items():
        summary = metric["summary"]
        range_min = summary["min"]
        range_max = summary["max"]
        finite = np.isfinite(float(range_min)) and np.isfinite(float(range_max))
        ranges[key] = {
            "variable": str(metric["variable"]),
            "units": str(metric["units"]),
            "range_min": range_min if finite else None,
            "range_max": range_max if finite else None,
            "range_width": float(range_max - range_min) if finite else None,
            "n_years": int(summary["n_years"]),
            "basis": "range of derived per-year target values",
            "temporal_context": str(metric["temporal_context"]),
        }
    return ranges


def extract_targets(args: argparse.Namespace) -> Dict[str, object]:
    path = Path(args.h0_file)
    if not path.exists():
        raise ValueError(f"h0 file does not exist: {path}")

    ds = Dataset(path)
    try:
        warnings: List[str] = []
        dates, date_source, date_warnings = decode_dates(ds, path, args.start_date)
        warnings.extend(date_warnings)
        years, year_warnings = complete_year_indices(dates)
        warnings.extend(year_warnings)

        selected = {
            "gpp": args.gpp_var,
            "et": args.et_var,
            "lai": args.lai_var,
            "root_biomass": args.root_var,
            "shoot_biomass": args.shoot_var,
            "canopy_height": args.canopy_height_var,
            "primary_root_depth": args.primary_root_depth_var,
            "vcmax25": args.vcmax_var,
            "jmax25": args.jmax_var,
            "sla": args.sla_var,
        }
        for key in (
            "gpp",
            "et",
            "lai",
            "root_biomass",
            "shoot_biomass",
            "canopy_height",
            "primary_root_depth",
            "vcmax25",
            "jmax25",
        ):
            require_variable(ds, selected[key], key)

        metrics: Dict[str, object] = {}
        for key, label in (("gpp", "annual_gpp"), ("et", "annual_et")):
            var = ds.variables[selected[key]]
            attrs = attrs_for(var)
            series = nanmean_flat_non_time(as_float_array(var), var.dimensions)
            method = infer_annual_method(selected[key], attrs, args.annual_method)
            values, metric_warnings = annual_values(series, years, method)
            metrics[label] = metric_record(
                label=label,
                variable=selected[key],
                units=str(attrs.get("units", "")),
                temporal_context="annual total",
                method=method,
                values=values,
                summary_stat=args.typical_stat,
                source_attrs=attrs,
                warnings=metric_warnings,
            )

        mid_start = args.midseason_start
        mid_end = args.midseason_end
        mid_specs = [
            ("lai", "midseason_lai", "mid-season state", "domain_mean"),
            ("root_biomass", "midseason_root_biomass", "mid-season summed active-PFT biomass", "sum_active_pfts"),
            ("shoot_biomass", "midseason_shoot_biomass", "mid-season summed active-PFT biomass", "sum_active_pfts"),
            ("canopy_height", "median_canopy_height", "mid-season median tallest active-PFT canopy height", "max_active_pfts"),
        ]
        for key, label, context, method in mid_specs:
            var = ds.variables[selected[key]]
            attrs = attrs_for(var)
            data = as_float_array(var)
            if method == "sum_active_pfts":
                series = pft_sum_series(data, var.dimensions)
            elif method == "max_active_pfts":
                series = max_flat_non_time_series(data, var.dimensions)
            else:
                series = nanmean_flat_non_time(data, var.dimensions)
            values = midseason_values(series, dates, years, mid_start, mid_end, args.midseason_stat)
            metrics[label] = metric_record(
                label=label,
                variable=selected[key],
                units=str(attrs.get("units", "")),
                temporal_context=context,
                method=f"{args.midseason_stat}_over_midseason_window",
                values=values,
                summary_stat=args.typical_stat,
                source_attrs=attrs,
            )

        var = ds.variables[selected["primary_root_depth"]]
        attrs = attrs_for(var)
        series = max_flat_non_time_series(as_float_array(var), var.dimensions)
        values = annual_state_values(series, years, "max")
        metrics["maximum_primary_root_depth"] = metric_record(
            label="maximum_primary_root_depth",
            variable=selected["primary_root_depth"],
            units=str(attrs.get("units", "")),
            temporal_context="maximum primary-root-tip depth",
            method="annual_max_over_primary_root_axes_and_active_pfts; max_across_complete_years",
            values=values,
            summary_stat="max",
            source_attrs=attrs,
        )

        weights, weight_dims, weight_method, weight_warnings = build_capacity_weights(ds, args)
        warnings.extend(weight_warnings)
        for key, label in (("vcmax25", "typical_vcmax25"), ("jmax25", "typical_jmax25")):
            var = ds.variables[selected[key]]
            attrs = attrs_for(var)
            series, used_weights = weighted_pft_series(as_float_array(var), var.dimensions, weights, weight_dims)
            actual_method = weight_method if used_weights else "active_pft_mean"
            values = midseason_values(series, dates, years, mid_start, mid_end, args.midseason_stat)
            metrics[label] = metric_record(
                label=label,
                variable=selected[key],
                units=str(attrs.get("units", "")),
                temporal_context="mid-season photosynthetic capacity at 25oC",
                method=f"{actual_method}; {args.midseason_stat}_over_midseason_window",
                values=values,
                summary_stat=args.typical_stat,
                source_attrs=attrs,
                weight_note=weight_method,
            )

        return {
            "schema_version": "1.0",
            "source_file": str(path),
            "date_source": date_source,
            "date_start": dates[0].isoformat(),
            "date_end": dates[-1].isoformat(),
            "complete_years_used": [int(year) for year in years],
            "midseason_window": {
                "start": f"{mid_start[0]:02d}-{mid_start[1]:02d}",
                "end": f"{mid_end[0]:02d}-{mid_end[1]:02d}",
                "per_year_statistic": args.midseason_stat,
            },
            "typical_statistic": args.typical_stat,
            "selected_variables": selected,
            "capacity_weight_method": weight_method,
            "target_units": collect_target_units(metrics),
            "target_ranges": collect_target_ranges(metrics),
            "warnings": warnings,
            "metrics": metrics,
        }
    finally:
        ds.close()


def metric_rows(result: Dict[str, object]) -> Iterable[Dict[str, object]]:
    for key in [
        "annual_gpp",
        "annual_et",
        "midseason_lai",
        "midseason_root_biomass",
        "midseason_shoot_biomass",
        "median_canopy_height",
        "maximum_primary_root_depth",
        "typical_vcmax25",
        "typical_jmax25",
    ]:
        metric = result["metrics"][key]
        summary = metric["summary"]
        yield {
            "metric": key,
            "variable": metric["variable"],
            "typical_value": summary["typical_value"],
            "range_min": summary["min"],
            "range_max": summary["max"],
            "mean": summary["mean"],
            "std": summary["std"],
            "min": summary["min"],
            "max": summary["max"],
            "n_years": summary["n_years"],
            "units": metric["units"],
            "method": metric["method"],
            "temporal_context": metric["temporal_context"],
        }


def write_json(result: Dict[str, object], out) -> None:
    json.dump(result, out, indent=2, allow_nan=True)
    out.write("\n")


def write_csv(result: Dict[str, object], out) -> None:
    fields = [
        "metric",
        "variable",
        "typical_value",
        "range_min",
        "range_max",
        "mean",
        "std",
        "min",
        "max",
        "n_years",
        "units",
        "method",
        "temporal_context",
    ]
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in metric_rows(result):
        writer.writerow(row)


def fmt(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return "nan"
    return f"{number:.6g}"


def md_escape(text: object) -> str:
    return str(text).replace("|", "\\|")


def write_markdown(result: Dict[str, object], out) -> None:
    out.write("# EcoSIM h0 Target Summary\n\n")
    out.write(f"- Source: `{result['source_file']}`\n")
    out.write(f"- Dates: {result['date_start']} to {result['date_end']} ({result['date_source']})\n")
    out.write("- Complete years: " + ", ".join(str(y) for y in result["complete_years_used"]) + "\n")
    window = result["midseason_window"]
    out.write(f"- Mid-season window: {window['start']} to {window['end']} ({window['per_year_statistic']} per year)\n")
    out.write(f"- Capacity weighting: {result['capacity_weight_method']}\n")
    if result["warnings"]:
        out.write("\n## Warnings\n\n")
        for warning in result["warnings"]:
            out.write(f"- {warning}\n")
    out.write("\n## Target Units\n\n")
    out.write("| metric | variable | units | temporal_context |\n")
    out.write("| --- | --- | --- | --- |\n")
    for metric, info in result["target_units"].items():
        out.write(
            "| "
            + " | ".join(
                [
                    md_escape(metric),
                    md_escape(info["variable"]),
                    md_escape(info["units"]),
                    md_escape(info["temporal_context"]),
                ]
            )
            + " |\n"
        )
    out.write("\n## Target Ranges\n\n")
    out.write("| metric | variable | range_min | range_max | units | basis |\n")
    out.write("| --- | --- | --- | --- | --- | --- |\n")
    for metric, info in result["target_ranges"].items():
        out.write(
            "| "
            + " | ".join(
                [
                    md_escape(metric),
                    md_escape(info["variable"]),
                    md_escape(fmt(info["range_min"])),
                    md_escape(fmt(info["range_max"])),
                    md_escape(info["units"]),
                    md_escape(info["basis"]),
                ]
            )
            + " |\n"
        )
    out.write("\n## Metrics\n\n")
    fields = ["metric", "variable", "typical_value", "range_min", "range_max", "mean", "std", "units", "method"]
    out.write("| " + " | ".join(fields) + " |\n")
    out.write("| " + " | ".join(["---"] * len(fields)) + " |\n")
    for row in metric_rows(result):
        out.write(
            "| "
            + " | ".join(
                md_escape(fmt(row[field]) if field in {"typical_value", "range_min", "range_max", "mean", "std"} else row[field])
                for field in fields
            )
            + " |\n"
        )


def open_output(path: Optional[Path]):
    if path is None:
        return sys.stdout
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8", newline="")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract typical annual GPP/ET and mid-season plant targets from EcoSIM h0 NetCDF output."
    )
    parser.add_argument("h0_file", type=Path, help="EcoSIM h0 NetCDF file.")
    parser.add_argument("--output", type=Path, help="Output file path. Defaults to stdout.")
    parser.add_argument("--format", choices=("json", "markdown", "csv"), default="markdown")
    parser.add_argument("--start-date", type=parse_date, help="Override inferred first date, YYYY-MM-DD.")
    parser.add_argument("--midseason-start", type=parse_mmdd, default=parse_mmdd("07-01"))
    parser.add_argument("--midseason-end", type=parse_mmdd, default=parse_mmdd("08-31"))
    parser.add_argument("--midseason-stat", choices=("median", "mean"), default="median")
    parser.add_argument("--typical-stat", choices=("median", "mean"), default="median")
    parser.add_argument(
        "--annual-method",
        choices=("auto", "year_end_cumulative", "max_cumulative", "diff_cumulative", "sum_interval"),
        default="auto",
        help="Annual total method for GPP and ET. Auto uses cumulative metadata when present.",
    )
    parser.add_argument(
        "--capacity-weight-method",
        choices=("auto", "shoot_sla_proxy", "active_pft_mean", "variable"),
        default="auto",
        help="How to combine PFT Vcmax/Jmax values.",
    )
    parser.add_argument("--capacity-weight-var", help="PFT weight variable when --capacity-weight-method variable.")
    parser.add_argument("--gpp-var", default=DEFAULT_VARS["gpp"])
    parser.add_argument("--et-var", default=DEFAULT_VARS["et"])
    parser.add_argument("--lai-var", default=DEFAULT_VARS["lai"])
    parser.add_argument("--root-var", default=DEFAULT_VARS["root_biomass"])
    parser.add_argument("--shoot-var", default=DEFAULT_VARS["shoot_biomass"])
    parser.add_argument("--canopy-height-var", default=DEFAULT_VARS["canopy_height"])
    parser.add_argument("--primary-root-depth-var", default=DEFAULT_VARS["primary_root_depth"])
    parser.add_argument("--vcmax-var", default=DEFAULT_VARS["vcmax25"])
    parser.add_argument("--jmax-var", default=DEFAULT_VARS["jmax25"])
    parser.add_argument("--sla-var", default=DEFAULT_VARS["sla"])
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = extract_targets(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    with open_output(args.output) as out:
        if args.format == "json":
            write_json(result, out)
        elif args.format == "csv":
            write_csv(result, out)
        else:
            write_markdown(result, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
