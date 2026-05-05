#!/usr/bin/env python3
"""
Extract a dominant-component soil profile from a CONUS gSSURGO file geodatabase
for a given longitude/latitude and interpolate selected properties to the vertical
layers used in a template CDL/netCDF text file.

The script uses vector lookup through MUPOLYGON to avoid relying on GDAL's
OpenFileGDB raster support. It is written to be robust to field-name casing in
file geodatabases, because some drivers expose columns such as MUKEY/COKEY/CHKEY
in upper case while others expose mukey/cokey/chkey.

Example
-------
python extract_gssurgo_profile.py \
  --gdb /path/to/gSSURGO_CONUS.gdb \
  --lon -121.85 --lat 39.0 \
  --template /path/to/template.nc.template \
  --out profile.json
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import pyogrio
from pyproj import CRS, Transformer
from shapely.geometry import Point

FILL = -999.9
EPS = 1e-6


@dataclass
class Horizon:
    top_m: float
    bottom_m: float
    chkey: str
    values: Dict[str, float]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--gdb", required=True, help="Path to gSSURGO_CONUS.gdb")
    p.add_argument("--lon", required=True, type=float)
    p.add_argument("--lat", required=True, type=float)
    p.add_argument(
        "--template",
        required=True,
        help="Path to template CDL text file containing CDPTH values",
    )
    p.add_argument("--out", required=True, help="Output JSON path")
    p.add_argument(
        "--extend-last",
        action="store_true",
        help="Extend deepest horizon downward to cover deeper template layers",
    )
    return p.parse_args()


def read_template_depths(template_path: str) -> np.ndarray:
    text = Path(template_path).read_text()
    m = re.search(r"CDPTH\s*=\s*(.*?);", text, flags=re.S)
    if not m:
        raise ValueError("Could not find CDPTH = ... ; block in template")
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", m.group(1))
    depths = np.array([float(x) for x in nums], dtype=float)
    depths = depths[depths > 0]
    if depths.size == 0:
        raise ValueError("No positive CDPTH values found in template")
    if not np.all(np.diff(depths) > 0):
        raise ValueError("Template CDPTH values must be strictly increasing")
    return depths


def get_layer_crs(gdb_path: str, layer: str) -> CRS:
    info = pyogrio.read_info(gdb_path, layer=layer)
    crs = info.get("crs")
    if crs is None:
        raise ValueError(f"No CRS found for layer {layer}")
    return CRS.from_user_input(crs)


def point_to_layer_crs(lon: float, lat: float, layer_crs: CRS) -> Tuple[float, float]:
    transformer = Transformer.from_crs("EPSG:4326", layer_crs, always_xy=True)
    return transformer.transform(lon, lat)


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with lower-case column names, preserving geometry."""
    out = df.copy()
    rename_map = {c: c.lower() for c in out.columns if isinstance(c, str)}
    return out.rename(columns=rename_map)


def first_present(mapping: Dict[str, str], candidates: Sequence[str]) -> Optional[str]:
    for name in candidates:
        if name.lower() in mapping:
            return mapping[name.lower()]
    return None


def field_map(gdb_path: str, layer: str) -> Dict[str, str]:
    """Map lower-case field name -> actual field name in the GDB layer."""
    info = pyogrio.read_info(gdb_path, layer=layer)
    fields = info.get("fields")
    if fields is None:
        raise ValueError(f"Could not inspect fields for layer {layer}")
    return {str(f).lower(): str(f) for f in fields}


def actual_columns(gdb_path: str, layer: str, requested: Sequence[str]) -> List[str]:
    fmap = field_map(gdb_path, layer)
    cols: List[str] = []
    missing: List[str] = []
    for req in requested:
        actual = fmap.get(req.lower())
        if actual is None:
            missing.append(req)
        else:
            cols.append(actual)
    if missing:
        raise ValueError(
            f"Layer {layer} is missing required field(s): {', '.join(missing)}. "
            f"Available fields include: {', '.join(list(fmap.values())[:30])}"
        )
    return cols


def read_point_mapunit(gdb_path: str, x: float, y: float) -> pd.Series:
    delta = 1.0
    bbox = (x - delta, y - delta, x + delta, y + delta)
    gdf = pyogrio.read_dataframe(gdb_path, layer="MUPOLYGON", bbox=bbox)
    if gdf.empty:
        raise ValueError("No MUPOLYGON features found at the requested location")
    gdf = canonicalize_columns(gdf)
    pt = Point(x, y)
    hits = gdf[gdf.geometry.contains(pt) | gdf.geometry.touches(pt)]
    if hits.empty:
        hits = gdf.assign(_dist=gdf.geometry.distance(pt)).sort_values("_dist").head(1)
    return hits.iloc[0]


def sql_string_list(values: Iterable[str]) -> str:
    return "(" + ",".join(["'" + str(v).replace("'", "''") + "'" for v in values]) + ")"


def choose_component(gdb_path: str, mukey: str) -> pd.Series:
    fmap = field_map(gdb_path, "component")
    actual_mukey = first_present(fmap, ["mukey"])
    if actual_mukey is None:
        raise ValueError("Layer component does not contain MUKEY/mukey")

    requested = ["mukey", "cokey", "compname", "comppct_r", "majcompflag"]
    available_requested = [r for r in requested if r.lower() in fmap]
    escaped_mukey = str(mukey).replace("'", "''")
    comp = pyogrio.read_dataframe(
        gdb_path,
        layer="component",
        where=f"{actual_mukey} = '{escaped_mukey}'",
        columns=actual_columns(gdb_path, "component", available_requested),
        read_geometry=False,
    )
    if comp.empty:
        raise ValueError(f"No component records found for mukey={mukey}")
    comp = canonicalize_columns(comp)

    if "majcompflag" in comp.columns:
        major = comp[comp["majcompflag"].astype(str).str.upper().eq("YES")]
        if not major.empty:
            comp = major

    sort_cols = [c for c in ["comppct_r", "cokey"] if c in comp.columns]
    ascending = [False if c == "comppct_r" else True for c in sort_cols]
    if sort_cols:
        comp = comp.sort_values(sort_cols, ascending=ascending)
    return comp.iloc[0]


def load_horizons(gdb_path: str, cokey: str) -> pd.DataFrame:
    hz_requested = [
        "cokey",
        "chkey",
        "hzdept_r",
        "hzdepb_r",
        "om_r",
        "dbovendry_r",
        "dbthirdbar_r",
        "dbfifteenbar_r",
        "wthirdbar_r",
        "wfifteenbar_r",
        "ksat_r",
        "sandtotal_r",
        "silttotal_r",
        "ph1to1h2o_r",
        "cec7_r",
    ]
    fmap = field_map(gdb_path, "chorizon")
    actual_cokey = first_present(fmap, ["cokey"])
    if actual_cokey is None:
        raise ValueError("Layer chorizon does not contain COKEY/cokey")

    escaped_cokey = str(cokey).replace("'", "''")
    hz = pyogrio.read_dataframe(
        gdb_path,
        layer="chorizon",
        where=f"{actual_cokey} = '{escaped_cokey}'",
        columns=actual_columns(gdb_path, "chorizon", hz_requested),
        read_geometry=False,
    )
    if hz.empty:
        raise ValueError(f"No chorizon records found for cokey={cokey}")
    hz = canonicalize_columns(hz)
    hz = hz.sort_values(["hzdept_r", "hzdepb_r", "chkey"]).reset_index(drop=True)

    chkeys = [str(x) for x in hz["chkey"].tolist()]
    try:
        fr_fmap = field_map(gdb_path, "chfrags")
        if "chkey" not in fr_fmap or "fragvol_r" not in fr_fmap:
            hz["fragvol_r"] = np.nan
            return hz
        fr = pyogrio.read_dataframe(
            gdb_path,
            layer="chfrags",
            where=f"{fr_fmap['chkey']} IN {sql_string_list(chkeys)}",
            columns=actual_columns(gdb_path, "chfrags", ["chkey", "fragvol_r"]),
            read_geometry=False,
        )
        if not fr.empty:
            fr = canonicalize_columns(fr)
            rock = fr.groupby("chkey", as_index=False)["fragvol_r"].sum()
            rock["fragvol_r"] = rock["fragvol_r"].clip(lower=0, upper=100)
            hz = hz.merge(rock, on="chkey", how="left")
        else:
            hz["fragvol_r"] = np.nan
    except Exception:
        hz["fragvol_r"] = np.nan

    return hz


def safe_float(x: object) -> float:
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def convert_horizons(hz: pd.DataFrame) -> List[Horizon]:
    out: List[Horizon] = []
    for _, r in hz.iterrows():
        top_m = float(r["hzdept_r"]) / 100.0
        bot_m = float(r["hzdepb_r"]) / 100.0
        if not np.isfinite(top_m) or not np.isfinite(bot_m) or bot_m <= top_m:
            continue

        dbod = safe_float(r.get("dbovendry_r"))
        db33 = safe_float(r.get("dbthirdbar_r"))
        db15 = safe_float(r.get("dbfifteenbar_r"))
        w33 = safe_float(r.get("wthirdbar_r"))
        w15 = safe_float(r.get("wfifteenbar_r"))
        om = safe_float(r.get("om_r"))
        ksat = safe_float(r.get("ksat_r"))
        sand = safe_float(r.get("sandtotal_r"))
        silt = safe_float(r.get("silttotal_r"))

        fc = np.nan
        wp = np.nan
        if np.isfinite(w33):
            bd_for_fc = db33 if np.isfinite(db33) else dbod
            if np.isfinite(bd_for_fc):
                fc = (w33 / 100.0) * bd_for_fc
        if np.isfinite(w15):
            bd_for_wp = db15 if np.isfinite(db15) else dbod
            if np.isfinite(bd_for_wp):
                wp = (w15 / 100.0) * bd_for_wp

        rock = safe_float(r.get("fragvol_r"))
        if np.isfinite(rock):
            rock /= 100.0

        corgc = np.nan
        if np.isfinite(om):
            corgc = om * 10.0 * 0.58

        vals = {
            "BKDSI": dbod,
            "FC": fc,
            "WP": wp,
            "SCNV": ksat * 3.6 if np.isfinite(ksat) else np.nan,
            "SCNH": ksat * 3.6 if np.isfinite(ksat) else np.nan,
            "CSAND": sand * 10.0 if np.isfinite(sand) else np.nan,
            "CSILT": silt * 10.0 if np.isfinite(silt) else np.nan,
            "ROCK": rock,
            "PH": safe_float(r.get("ph1to1h2o_r")),
            "CEC": safe_float(r.get("cec7_r")),
            "CORGC": corgc,
            "OM": om,
        }
        out.append(Horizon(top_m=top_m, bottom_m=bot_m, chkey=str(r["chkey"]), values=vals))
    if not out:
        raise ValueError("No usable horizon intervals found")
    return out


def interpolate_profile(
    horizons: Sequence[Horizon],
    target_bottoms: Sequence[float],
    varname: str,
    log_interp: bool = False,
    extend_last: bool = False,
) -> List[float]:
    target_bottoms = np.asarray(target_bottoms, dtype=float)
    target_tops = np.concatenate(([0.0], target_bottoms[:-1]))
    results: List[float] = []

    src = [(h.top_m, h.bottom_m, safe_float(h.values.get(varname))) for h in horizons]
    if extend_last and src:
        last_top, last_bot, last_val = src[-1]
        if target_bottoms[-1] > last_bot and np.isfinite(last_val):
            src = list(src) + [(last_bot, float(target_bottoms[-1]), last_val)]

    for ttop, tbot in zip(target_tops, target_bottoms):
        overlaps = []
        weights = []
        for stop, sbot, sval in src:
            if not np.isfinite(sval):
                continue
            overlap = min(tbot, sbot) - max(ttop, stop)
            if overlap > 0:
                overlaps.append(sval)
                weights.append(overlap)
        if not weights:
            results.append(FILL)
            continue
        w = np.asarray(weights, dtype=float)
        v = np.asarray(overlaps, dtype=float)
        if log_interp:
            vv = np.maximum(v, EPS)
            agg = float(np.exp(np.average(np.log(vv), weights=w)))
        else:
            agg = float(np.average(v, weights=w))
        results.append(agg)
    return results


def finite_or_none(x: float) -> Optional[float]:
    x = safe_float(x)
    return None if not np.isfinite(x) else float(x)


def main() -> None:
    args = parse_args()
    target_depths = read_template_depths(args.template)
    layer_crs = get_layer_crs(args.gdb, "MUPOLYGON")
    x, y = point_to_layer_crs(args.lon, args.lat, layer_crs)
    poly = read_point_mapunit(args.gdb, x, y)

    if "mukey" not in poly.index:
        raise ValueError(
            "MUPOLYGON lookup succeeded, but MUKEY/mukey was not found in the returned fields. "
            f"Fields returned: {', '.join(map(str, poly.index.tolist()))}"
        )
    mukey = str(poly["mukey"])

    comp = choose_component(args.gdb, mukey)
    if "cokey" not in comp.index:
        raise ValueError(
            "Component lookup succeeded, but COKEY/cokey was not found in the returned fields. "
            f"Fields returned: {', '.join(map(str, comp.index.tolist()))}"
        )
    cokey = str(comp["cokey"])

    hzdf = load_horizons(args.gdb, cokey)
    horizons = convert_horizons(hzdf)

    output = {
        "input": {
            "gdb": str(args.gdb),
            "lon": args.lon,
            "lat": args.lat,
            "template": str(args.template),
            "extend_last": bool(args.extend_last),
        },
        "selection": {
            "mukey": mukey,
            "cokey": cokey,
            "component_name": str(comp.get("compname", "")),
            "component_pct_r": finite_or_none(comp.get("comppct_r")),
        },
        "source_horizons": [
            {
                "top_m": h.top_m,
                "bottom_m": h.bottom_m,
                "chkey": h.chkey,
                **{k: finite_or_none(v) for k, v in h.values.items()},
            }
            for h in horizons
        ],
        "template_depths_m": target_depths.tolist(),
        "interpolated": {
            "CDPTH": target_depths.tolist(),
            "BKDSI": interpolate_profile(horizons, target_depths, "BKDSI", extend_last=args.extend_last),
            "FC": interpolate_profile(horizons, target_depths, "FC", extend_last=args.extend_last),
            "WP": interpolate_profile(horizons, target_depths, "WP", extend_last=args.extend_last),
            "SCNV": interpolate_profile(horizons, target_depths, "SCNV", extend_last=args.extend_last),
            "SCNH": interpolate_profile(horizons, target_depths, "SCNH", extend_last=args.extend_last),
            "CSAND": interpolate_profile(horizons, target_depths, "CSAND", extend_last=args.extend_last),
            "CSILT": interpolate_profile(horizons, target_depths, "CSILT", extend_last=args.extend_last),
            "ROCK": interpolate_profile(horizons, target_depths, "ROCK", extend_last=args.extend_last),
            "PH": interpolate_profile(horizons, target_depths, "PH", extend_last=args.extend_last),
            "CEC": interpolate_profile(horizons, target_depths, "CEC", extend_last=args.extend_last),
            "CORGC": interpolate_profile(horizons, target_depths, "CORGC", log_interp=True, extend_last=args.extend_last),
            "OM_percent": interpolate_profile(horizons, target_depths, "OM", log_interp=True, extend_last=args.extend_last),
        },
        "notes": {
            "BKDSI_source": "dbovendry_r",
            "FC_formula": "(wthirdbar_r / 100) * dbthirdbar_r",
            "WP_formula": "(wfifteenbar_r / 100) * dbfifteenbar_r",
            "SCN_formula": "ksat_r [um/s] * 3.6 => mm/h",
            "CSAND_CSILT_formula": "percent * 10 => kg/Mg",
            "ROCK_source": "sum(chfrags.fragvol_r) / 100",
            "CORGC_formula": "om_r [%] * 10 * 0.58 => kg C / Mg soil",
            "CORGC_interpolation": "overlap-weighted geometric mean on target layers",
        },
    }

    Path(args.out).write_text(json.dumps(output, indent=2))
    print(
        json.dumps(
            {
                "mukey": mukey,
                "cokey": cokey,
                "component_name": output["selection"]["component_name"],
                "component_pct_r": output["selection"]["component_pct_r"],
                "out": str(args.out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
