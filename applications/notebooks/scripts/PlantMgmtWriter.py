#!/usr/bin/env python3
"""
Write an EcoSIM plant management NetCDF file from JSON input.

JSON format expected:
- top-level: pft_dflag, years (optional/incomplete), topo_units
- planting block:
    DDMMYYYY
    Planting_population
    Planting_depth
- mgmt block:
    DDMMYYYY
    iHarvType
    jHarvType
    CutHeight
    FractionCut           #fraction of population removed for non-grazing, grazing rate for herbivore
    FineFractionLeafHarvested_pft
    FineFractionNonleafHarvested_pft
    StalkFractionHarvested_pft
    StandeadFractionHarvested_pft
    FineFractionLeafHarvested_col
    FineFractionNonleafHarvested_col
    StalkFractionHarvested_col
    StandeadFractionHarvested_col

Output string formats:
- pft_pltinfo:
    "DDMMYYYY Planting_population Planting_depth"
- each pft_mgmt line:
    "DDMMYYYY,iHarvType,jHarvType,CutHeight,FractionCut,
     FineFractionLeafHarvested_pft,FineFractionNonleafHarvested_pft,
     WoodyFractionHarvested_pft,StandeadFractionHarvested_pft,
     FineFractionLeafHarvested_col,FineFractionNonleafHarvested_col,
     WoodyFractionHarvested_col,StandeadFractionHarvested_col"
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
from netCDF4 import Dataset, stringtochar


STRING10 = 10
STRING128 = 128
DEFAULT_FILL_SHORT = -9999


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pad_or_truncate(value: Any, max_len: int) -> str:
    s = "" if value is None else str(value)
    return s[:max_len].ljust(max_len)


def write_fixed_strlen(var, data: np.ndarray, strlen: int) -> None:
    arr = np.asarray(data, dtype=f"S{strlen}")
    var[:] = stringtochar(arr)


def fmt_date_ddmmyyyy(value: Any) -> str:
    if isinstance(value, dict):
        dd = int(value["DD"])
        mm = int(value["MM"])
        yyyy = int(value["YYYY"])
        out = f"{dd:02d}{mm:02d}{yyyy:04d}"
    else:
        out = str(value).strip()

    if len(out) != 8 or not out.isdigit():
        raise ValueError(f"Invalid DDMMYYYY date: {value}")
    return out


def fmt_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    return str(value).strip()


def collect_years(cfg: Dict[str, Any]) -> List[int]:
    """
    Use top-level years if they fully cover the nested years.
    Otherwise derive the complete sorted year list from topo_units[*].years keys.
    """
    top_years = [int(y) for y in cfg.get("years", [])]

    nested_years = set()
    for tu in cfg.get("topo_units", []):
        for y in tu.get("years", {}).keys():
            nested_years.add(int(y))

    if not nested_years:
        if top_years:
            return sorted(top_years)
        raise ValueError("No years found in JSON.")

    nested_sorted = sorted(nested_years)

    if not top_years:
        return nested_sorted

    if set(top_years) != nested_years:
        return nested_sorted

    return sorted(top_years)


def build_pft_pltinfo(pft: Dict[str, Any]) -> str:
    planting = pft.get("planting", {})
    if not planting:
        return ""

    date_str = fmt_date_ddmmyyyy(planting["DDMMYYYY"])
    population = fmt_number(planting["Planting_population"])
    depth = fmt_number(planting["Planting_depth"])
    return f"{date_str} {population} {depth}"


def build_mgmt_line(mgmt: Dict[str, Any]) -> str:
    fields = [
        fmt_date_ddmmyyyy(mgmt["DDMMYYYY"]),
        fmt_number(mgmt["iHarvType"]),
        fmt_number(mgmt["jHarvType"]),
        fmt_number(mgmt["CutHeight"]),
        fmt_number(mgmt["FractionCut"]),
        fmt_number(mgmt["FineFractionLeafHarvested_pft"]),
        fmt_number(mgmt["FineFractionNonleafHarvested_pft"]),
        fmt_number(mgmt["StalkFractionHarvested_pft"]),
        fmt_number(mgmt["StandeadFractionHarvested_pft"]),
        fmt_number(mgmt["FineFractionLeafHarvested_col"]),
        fmt_number(mgmt["FineFractionNonleafHarvested_col"]),
        fmt_number(mgmt["StalkFractionHarvested_col"]),
        fmt_number(mgmt["StandeadFractionHarvested_col"]),
    ]
    return ",".join(fields)


def infer_dimensions(cfg: Dict[str, Any], years: List[int]) -> Dict[str, int]:
    topo_units = cfg["topo_units"]

    ntopou = len(topo_units)
    nyear = len(years)
    maxpfts = 5
    maxpmgt = 24

#    for tu in topo_units:
#        year_map = tu.get("years", {})
#        for y in years:
#            year_block = year_map.get(str(y), {})
#            pfts = year_block.get("pfts", [])
#            maxpfts = max(maxpfts, len(pfts))
#            for pft in pfts:
#                maxpmgt = max(maxpmgt, len(pft.get("mgmt", [])))

    return {
        "ntopou": ntopou,
        "year": nyear,
        "maxpfts": maxpfts,
        "maxpmgt": maxpmgt,
    }


def validate_config(cfg: Dict[str, Any]) -> None:
    if "topo_units" not in cfg or not isinstance(cfg["topo_units"], list) or not cfg["topo_units"]:
        raise ValueError("'topo_units' must be a non-empty list")

    for i, tu in enumerate(cfg["topo_units"]):
        for key in ["NH1", "NV1", "NH2", "NV2", "NZ"]:
            if key not in tu:
                raise ValueError(f"topo_units[{i}] missing required key: {key}")


def create_nc(json_cfg: Dict[str, Any], out_path: str | Path) -> None:
    validate_config(json_cfg)
    years = collect_years(json_cfg)
    dims = infer_dimensions(json_cfg, years)

    topo_units: List[Dict[str, Any]] = json_cfg["topo_units"]
    pft_dflag = int(json_cfg.get("pft_dflag", 1))

    with Dataset(out_path, "w", format="NETCDF4_CLASSIC") as ds:
        ds.createDimension("ntopou", dims["ntopou"])
        ds.createDimension("year", dims["year"])
        ds.createDimension("maxpfts", dims["maxpfts"])
        ds.createDimension("maxpmgt", dims["maxpmgt"])
        ds.createDimension("string10", STRING10)
        ds.createDimension("string128", STRING128)

        v_NH1 = ds.createVariable("NH1", "i4", ("ntopou",))
        v_NV1 = ds.createVariable("NV1", "i4", ("ntopou",))
        v_NH2 = ds.createVariable("NH2", "i4", ("ntopou",))
        v_NV2 = ds.createVariable("NV2", "i4", ("ntopou",))
        v_NZ = ds.createVariable("NZ", "i4", ("ntopou",))
        v_year = ds.createVariable("year", "i4", ("year",))
        v_nmgnts = ds.createVariable(
            "nmgnts",
            "i2",
            ("year", "ntopou", "maxpfts"),
            fill_value=DEFAULT_FILL_SHORT,
        )
        v_pft_type = ds.createVariable(
            "pft_type", "S1", ("year", "ntopou", "maxpfts", "string10")
        )
        v_pft_pltinfo = ds.createVariable(
            "pft_pltinfo", "S1", ("year", "ntopou", "maxpfts", "string128")
        )
        v_pft_mgmt = ds.createVariable(
            "pft_mgmt", "S1", ("year", "ntopou", "maxpfts", "maxpmgt", "string128")
        )
        v_pft_dflag = ds.createVariable("pft_dflag", "i4")

        v_year[:] = np.array(years, dtype=np.int32)
        v_NH1[:] = np.array([tu["NH1"] for tu in topo_units], dtype=np.int32)
        v_NV1[:] = np.array([tu["NV1"] for tu in topo_units], dtype=np.int32)
        v_NH2[:] = np.array([tu["NH2"] for tu in topo_units], dtype=np.int32)
        v_NV2[:] = np.array([tu["NV2"] for tu in topo_units], dtype=np.int32)
        v_NZ[:] = np.array([tu["NZ"] for tu in topo_units], dtype=np.int32)
        v_pft_dflag.assignValue(pft_dflag)
        v_nmgnts[:] = DEFAULT_FILL_SHORT
        print('here1')

        pft_type_data = np.full(
            (dims["year"], dims["ntopou"], dims["maxpfts"]),
            "",
            dtype=f"U{STRING10}",
        )
        pft_pltinfo_data = np.full(
            (dims["year"], dims["ntopou"], dims["maxpfts"]),
            "",
            dtype=f"U{STRING128}",
        )
        pft_mgmt_data = np.full(
            (dims["year"], dims["ntopou"], dims["maxpfts"], dims["maxpmgt"]),
            "",
            dtype=f"U{STRING128}",
        )

        for itu, tu in enumerate(topo_units):
            year_blocks = tu.get("years", {})

            for iy, year_val in enumerate(years):
                yblock = year_blocks.get(str(year_val), {})
                pfts = yblock.get("pfts", [])

                for ipft, pft in enumerate(pfts):
                    pft_type_data[iy, itu, ipft] = pad_or_truncate(
                        pft.get("pft_type", ""),
                        STRING10,
                    )

                    pltinfo_str = build_pft_pltinfo(pft)
                    pft_pltinfo_data[iy, itu, ipft] = pad_or_truncate(
                        pltinfo_str,
                        STRING128,
                    )

                    mgmts = pft.get("mgmt", [])
                    v_nmgnts[iy, itu, ipft] = len(mgmts)

                    for im, mgmt in enumerate(mgmts):
                        mgmt_line = build_mgmt_line(mgmt)
                        pft_mgmt_data[iy, itu, ipft, im] = pad_or_truncate(
                            mgmt_line,
                            STRING128,
                        )
        write_fixed_strlen(v_pft_type, pft_type_data, STRING10)
        write_fixed_strlen(v_pft_pltinfo, pft_pltinfo_data, STRING128)
        write_fixed_strlen(v_pft_mgmt, pft_mgmt_data, STRING128)

        ds.description = f"PFT input data created on {datetime.now():%Y-%m-%d %H:%M:%S}"


def PlantMgmtWriter(in_json, out_nc):
    cfg = load_json(in_json)
    create_nc(cfg, out_nc)
    print(f"Wrote NetCDF file: {out_nc}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python PlantMgmtWriter.py input.json output.nc")
        raise SystemExit(1)

    PlantMgmtWriter(sys.argv[1], sys.argv[2])