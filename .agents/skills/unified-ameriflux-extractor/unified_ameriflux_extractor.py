#!/usr/bin/env python3
"""Unified AmeriFlux site extraction script.

Combines four functionalities:
1. Extract site metadata (lat, lon, elevation, MAT, climate code, IGBP type) from the AmeriFlux website using a local vision model.
2. Extract NADP atmospheric chemistry data for a range of years.
3. Extract tDEP atmospheric deposition data for a range of years.
4. Extract a dominant-component soil profile from a gSSURGO geodatabase (via ameriflux-surgo-grid-extract skill).

The script produces a single JSON file containing site information and per‑year NADP, tDEP, and gSSURGO data.
"""

import os
import sys
import json
import argparse
import base64
import requests
import subprocess
import math
from typing import Dict, Any, Optional

# --- Vision extraction (from ameriflux_site_info) ---
from playwright.sync_api import sync_playwright

# Koppen mapping (from ameriflux_site_info)
KOPPEN_MAP = {
    "Af": 11, "Am": 12, "As": 13, "Aw": 14, "BWk": 21, "BWh": 22, "BSk": 26, "BSh": 27,
    "Cfa": 31, "Cfb": 32, "Cfc": 33, "Csa": 34, "Csb": 35, "Csc": 36, "Cwa": 37, "Cwb": 38, "Cwc": 39,
    "Dfa": 41, "Dfb": 42, "Dfc": 43, "Dfd": 44, "Dsa": 45, "Dsb": 46, "Dsc": 47, "Dsd": 48,
    "Dwa": 49, "Dwb": 50, "Dwc": 51, "Dwd": 52, "ET": 61, "EF": 62,
}


def encode_image(image_path: str) -> str:
    """Base64‑encode an image for the Ollama vision endpoint."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def query_vision_model(image_path: str, site_id: str) -> Optional[Dict[str, Any]]:
    """Send screenshot to local Qwen2.5‑VL model and parse JSON output."""
    base64_image = encode_image(image_path)
    prompt = (
        f"Analyze this screenshot of AmeriFlux site {site_id}. "
        "Extract the following values and return them in a strict JSON format: "
        "latitude, longitude, elevation, MAT, climate_code (e.g., BSk, Af), "
        "igbp_type (e.g., GRA, ENF, DBF). Only return the JSON object."
    )
    payload = {
        "model": "qwen2.5vl:7b",
        "messages": [{"role": "user", "content": prompt, "images": [base64_image]}],
        "stream": False,
    }
    try:
        resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        # Strip possible markdown fences
        json_str = content.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"Vision model query failed: {e}", file=sys.stderr)
        return None


def map_vegetation(igbp: str) -> int:
    """Map IGBP type to EcoSIM integer (ENF→11, DBF→10, else 10)."""
    igbp = str(igbp).upper()
    if "ENF" in igbp:
        return 11
    if "DBF" in igbp:
        return 10
    return 10  # default fallback


def extract_site_info(site_id: str, output_dir: str = "result") -> Optional[Dict[str, Any]]:
    """Capture a screenshot of the AmeriFlux site page and extract metadata.

    Returns a dict with EcoSIM variable keys (ALATG, ALONG, ALTIG, ATCAG, IETYPG, IXTYP1).
    """
    url = f"https://ameriflux.lbl.gov/sites/siteinfo/{site_id}"
    img_path = os.path.join(output_dir, "images", f"{site_id}_screenshot.png")
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1600})
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=img_path)
            browser.close()
    except Exception as e:
        print(f"Failed to capture screenshot: {e}", file=sys.stderr)
        return None

    raw = query_vision_model(img_path, site_id)
    if not raw:
        return None
    final_json = {
        "site_name": site_id,
        "ALATG": float(raw.get("latitude", 0.0)),
        "ALONG": float(raw.get("longitude", 0.0)),
        "ALTIG": float(raw.get("elevation", 0.0)),
        "ATCAG": float(raw.get("MAT", 0.0)),
        "IETYPG": KOPPEN_MAP.get(raw.get("climate_code"), 0),
        "IXTYP1": map_vegetation(raw.get("igbp_type", "")),
        "_raw": raw,
    }
    return final_json

# --- NADP extraction (from extract_nadp_range.py) ---
import rasterio
from pyproj import Transformer

ELEMENTAL_CONVERSIONS = {
    "so4": 0.3338,
    "no3": 0.2259,
    "nh4": 0.7765,
}
ION_LIST = ["phlab", "so4", "no3", "nh4", "ca", "mg", "na", "k", "cl"]
VALID_EXT = [".tif", ".asc", ".TIF", ".ASC"]


def is_valid_nadp_value(ion: str, value: Any) -> bool:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(value) or value <= -900 or abs(value) >= 1e20:
        return False
    if ion == "phlab":
        return 0.0 <= value <= 14.0
    return value >= 0.0


def extract_nadp_range(lat: float, lon: float, base_dir: str, start_year: int, end_year: int) -> Dict[str, Any]:
    results = {
        "metadata": {
            "requested_lat": lat,
            "requested_lon": lon,
            "years": list(range(start_year, end_year + 1)),
        },
        "data_by_year": {},
    }
    for year in range(start_year, end_year + 1):
        year_str = str(year)
        year_root = os.path.join(base_dir, year_str)
        if not os.path.isdir(year_root):
            continue
        year_data = {"raw_ion_conc": {}, "elemental_conc": {}}
        for ion in ION_LIST:
            folder_variants = ["pH"] if ion == "phlab" else [ion.upper(), ion.capitalize()]
            grid_file = None
            for variant in folder_variants:
                sub_folder = f"{variant}_conc_{year_str}"
                file_prefix = f"conc_{ion.lower()}_{year_str}"
                for ext in VALID_EXT:
                    candidate = os.path.join(year_root, sub_folder, f"{file_prefix}{ext}")
                    if os.path.isfile(candidate):
                        grid_file = candidate
                        break
                if grid_file:
                    break
            if not grid_file:
                continue
            try:
                with rasterio.open(grid_file) as src:
                    if src.crs and not src.crs.is_geographic:
                        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                        tx, ty = transformer.transform(lon, lat)
                    else:
                        tx, ty = lon, lat
                    row, col = src.index(tx, ty)
                    if 0 <= row < src.height and 0 <= col < src.width:
                        val = src.read(1)[row, col]
                        if is_valid_nadp_value(ion, val):
                            key = f"{ion}_mg_l" if ion != "phlab" else "ph"
                            year_data["raw_ion_conc"][key] = float(val)
                            if ion in ELEMENTAL_CONVERSIONS:
                                element_val = val * ELEMENTAL_CONVERSIONS[ion]
                                element_key = f"{ion}_as_element_mg_l"
                                year_data["elemental_conc"][element_key] = float(element_val)
            except Exception as e:
                print(f"NADP extraction error year {year} ion {ion}: {e}", file=sys.stderr)
        results["data_by_year"][year_str] = year_data
    return results

# --- tDEP extraction (from extract_tdep_from_dir.py) ---

TDEP_VAR_MAP = {
    "CN4RIG": "nh4_ww",
    "CNORIG": "no3_ww",
    "CSORG": "s_ww",
    "CCARG": "ca_ww",
    "CMGRG": "mg_ww",
    "CNARG": "na_ww",
    "CKARG": "k_ww",
    "CCLRG": "cl_ww",
    "RAINH": "precip_ww",
}

TDEP_CRS = (
    "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 "
    "+x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
)


def extract_tdep_range(lat: float, lon: float, base_dir: str, start_year: int, end_year: int) -> Dict[str, Any]:
    results = {
        "metadata": {
            "requested_lat": lat,
            "requested_lon": lon,
            "years": list(range(start_year, end_year + 1)),
        },
        "data_by_year": {},
    }
    try:
        transformer = Transformer.from_crs("EPSG:4326", TDEP_CRS, always_xy=True)
        tx, ty = transformer.transform(lon, lat)
    except Exception as e:
        print(f"Coordinate transform error for tDEP: {e}", file=sys.stderr)
        return results

    for year in range(start_year, end_year + 1):
        year_str = str(year)
        year_dir = os.path.join(base_dir, f"tDEP-{year_str}")
        if not os.path.isdir(year_dir):
            continue
        year_data = {"raw_values": {}, "converted_concentrations": {}}
        files = os.listdir(year_dir)
        # Precipitation first (RAINH)
        precip_file = next((f for f in files if f.startswith("precip_ww") and f.endswith('.tif')), None)
        precip_m = None
        if precip_file:
            with rasterio.open(os.path.join(year_dir, precip_file)) as src:
                precip_val = next(src.sample([(tx, ty)]))[0]
                if 0 <= precip_val < 1e10:
                    year_data["raw_values"]["RAINH"] = float(precip_val)
                    precip_m = precip_val / 100.0  # cm -> m
        # Other variables
        for tmpl_var, tdep_prefix in TDEP_VAR_MAP.items():
            if tmpl_var == "RAINH":
                continue
            target_file = next((f for f in files if f.startswith(tdep_prefix) and f.endswith('.tif')), None)
            if not target_file:
                continue
            with rasterio.open(os.path.join(year_dir, target_file)) as src:
                val = next(src.sample([(tx, ty)]))[0]
                year_data["raw_values"][tmpl_var] = float(val)
                if precip_m and precip_m > 0:
                    conc = (val * 0.1) / precip_m  # kg/ha -> g/m3 (approx)
                    year_data["converted_concentrations"][tmpl_var] = float(conc)
        results["data_by_year"][year_str] = year_data
    return results

# --- gSSURGO extraction wrapper ---

def run_gssurgo_extraction(gdb_path: str, lon: float, lat: float, template_path: str, out_path: str, extend_last: bool = False) -> Optional[Dict[str, Any]]:
    """Execute the ameriflux-surgo-grid-extract skill script and return parsed JSON.

    Parameters
    ----------
    gdb_path: Path to the gSSURGO_CONUS.gdb file.
    lon, lat: Coordinates for the site.
    template_path: Path to the template NetCDF file containing CDPTH values.
    out_path: Destination JSON output file.
    extend_last: Whether to extend the deepest horizon.

    Returns
    -------
    Parsed JSON dict from the skill output, or ``None`` if the extraction fails.
    """
    cmd = [sys.executable, ".agents/skills/ameriflux-surgo-grid-extract/extract_gssurgo_profile.py",
           "--gdb", gdb_path,
           "--lon", str(lon), "--lat", str(lat),
           "--template", template_path,
           "--out", out_path]
    if extend_last:
        cmd.append("--extend-last")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"gSSURGO extraction failed: {result.stderr}", file=sys.stderr)
        return None
    try:
        with open(out_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read gSSURGO output JSON: {e}", file=sys.stderr)
        return None

# --- Unified workflow ---

def run_unified_extraction(
    site_id: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    nadp_dir: str = "",
    tdep_dir: str = "",
    start_year: int = 0,
    end_year: int = 0,
    output_file: str = "result/unified_site_data.json",
    gssurgo_gdb: str = "",
    gssurgo_template: str = "",
    gssurgo_out: str = "",
    gssurgo_extend_last: bool = False,
    climate_output: str = "",
    grid_output: str = "",
    climate_data_dir: str = "data",
    result_dir: str = "result",
) -> None:
    # Resolve coordinates
    if site_id:
        site_info = extract_site_info(site_id)
        if not site_info:
            sys.exit(1)
        lat = site_info["ALATG"]
        lon = site_info["ALONG"]
    else:
        if lat is None or lon is None:
            print("Latitude and longitude required when no site_id is provided.", file=sys.stderr)
            sys.exit(1)
        site_info = {}
    # NADP extraction
    nadp_results = {}
    if nadp_dir:
        nadp_results = extract_nadp_range(lat, lon, nadp_dir, start_year, end_year)
    # tDEP extraction
    tdep_results = {}
    if tdep_dir:
        tdep_results = extract_tdep_range(lat, lon, tdep_dir, start_year, end_year)
    # gSSURGO extraction if provided
    gssurgo_result = {}
    if gssurgo_gdb and gssurgo_template and gssurgo_out:
        gssurgo_result = run_gssurgo_extraction(
            gssurgo_gdb, lon, lat, gssurgo_template, gssurgo_out, gssurgo_extend_last
        ) or {}
    # Merge all
    unified = {
        "site_id": site_id or "custom_coordinates",
        "site_metadata": site_info,
        "nadp": nadp_results,
        "tdep": tdep_results,
        "gssurgo": gssurgo_result,
    }
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(unified, f, indent=4)
    print(f"Unified extraction complete. Output written to {output_file}")
    # Generate EcoSIM climate forcing NetCDF if requested
    if climate_output:
        climate_script_path = os.path.join(os.getcwd(), "Tools", "create_ecosim_climate_forcing.py")
        climate_cmd = [sys.executable, climate_script_path, site_id or ""]
        if climate_output:
            climate_cmd.extend(["--output", climate_output])
        climate_cmd.extend(["--data-dir", climate_data_dir, "--result-dir", result_dir])
        result = subprocess.run(climate_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"EcoSIM climate forcing generation failed: {result.stderr}", file=sys.stderr)
        else:
            output_path = climate_output if climate_output else os.path.join(result_dir, f"{site_id}_ecosim_climate.nc")
            print(f"EcoSIM climate forcing generated: {output_path}")
    # Generate EcoSIM grid forcing NetCDF if requested
    if grid_output:
        grid_script_path = os.path.join(os.getcwd(), "Tools", "create_ecosim_grid_forcing.py")
        grid_cmd = [sys.executable, grid_script_path, site_id or ""]
        result = subprocess.run(grid_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"EcoSIM grid forcing generation failed: {result.stderr}", file=sys.stderr)
        else:
            default_grid_path = os.path.join(result_dir, f"{site_id}_ecosim_grid.nc")
            if os.path.abspath(grid_output) != os.path.abspath(default_grid_path):
                try:
                    os.rename(default_grid_path, grid_output)
                    print(f"EcoSIM grid forcing moved to {grid_output}")
                except Exception as e:
                    print(f"Failed to move grid output: {e}", file=sys.stderr)
            else:
                print(f"EcoSIM grid forcing generated: {default_grid_path}")


def main():
    parser = argparse.ArgumentParser(description="Unified AmeriFlux site and EcoSIM forcing data extraction.")
    parser.add_argument("--site-id", help="AmeriFlux site identifier (e.g., US-XXX).")
    parser.add_argument("--latitude", type=float, help="Latitude (used if site-id not provided).")
    parser.add_argument("--longitude", type=float, help="Longitude (used if site-id not provided).")
    parser.add_argument("--nadp-input", required=True, help="Base directory for NADP year folders.")
    parser.add_argument("--tdep-input", required=True, help="Base directory for tDEP year folders.")
    parser.add_argument("--year1", type=int, required=True, help="Start year (inclusive).")
    parser.add_argument("--year2", type=int, required=True, help="End year (inclusive).")
    parser.add_argument("--gssurgo-gdb", help="Path to gSSURGO_CONUS.gdb file.")
    parser.add_argument("--gssurgo-template", help="Path to template NetCDF file for CDPTH values.")
    parser.add_argument("--gssurgo-out", help="Destination JSON output for gSSURGO extraction.")
    parser.add_argument("--gssurgo-extend-last", action="store_true", help="Extend deepest horizon in gSSURGO extraction.")
    parser.add_argument("--output", default="result/unified_site_data.json", help="Path to final JSON output.")
    parser.add_argument("--climate-output", help="Path to EcoSIM climate forcing NetCDF output.")
    parser.add_argument("--grid-output", help="Path to EcoSIM grid forcing NetCDF output.")
    parser.add_argument("--climate-data-dir", default="data", help="Data directory for climate forcing (contains ERA5 files).")
    parser.add_argument("--result-dir", default="result", help="Directory for intermediate results and output files.")
    args = parser.parse_args()

    run_unified_extraction(
        site_id=args.site_id,
        lat=args.latitude,
        lon=args.longitude,
        nadp_dir=args.nadp_input,
        tdep_dir=args.tdep_input,
        start_year=args.year1,
        end_year=args.year2,
        output_file=args.output,
        gssurgo_gdb=args.gssurgo_gdb or "",
        gssurgo_template=args.gssurgo_template or "",
        gssurgo_out=args.gssurgo_out or "",
        gssurgo_extend_last=args.gssurgo_extend_last,
        climate_output=args.climate_output or "",
        grid_output=args.grid_output or "",
        climate_data_dir=args.climate_data_dir,
        result_dir=args.result_dir,
    )

if __name__ == "__main__":
    main()
