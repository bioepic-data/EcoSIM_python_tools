---
name: unified-ameriflux-extractor
description: Run the combined AmeriFlux to EcoSIM extraction workflow for site metadata, NADP or tDEP atmospheric chemistry, gSSURGO soil data, and optional climate or grid NetCDF forcing. Use when building a complete site-specific EcoSIM input package.
---

# Unified AmeriFlux Extractor

## Use When

- You need a complete EcoSIM input package for an AmeriFlux site.
- You want one workflow to combine site metadata, atmospheric chemistry, tDEP deposition, gSSURGO soil profile data, and optional NetCDF forcing files.
- You need derivation reports for climate or grid variables left at fill/default values.

## Constraints
- Do not extract climate data beyond site metadata (the script only extracts site metadata, NADP, tDEP, and gSSURGO soil data).
- Requires local Ollama vision model `qwen2.5vl:7b` to be running.

## Workflow

1. Resolve site metadata with `ameriflux-site-info`.
2. Extract NADP and tDEP chemistry with `ameriflux-atmchem-info`.
3. Extract soil profile data with `ameriflux-surgo-grid-extract` when gSSURGO inputs are provided.
4. Optionally invoke `Tools/create_ecosim_climate_forcing.py` or `Tools/create_ecosim_grid_forcing.py`.
5. Write merged JSON and site-specific outputs under `result/<SITE_ID>/`.

## Purpose
Combine multiple AmeriFlux data extraction capabilities into a single workflow:
1. Retrieve site metadata (latitude, longitude, elevation, mean annual temperature, Koppen climate code, IGBP vegetation type) from the AmeriFlux website using a vision model (RAG).
2. Extract atmospheric chemistry (NADP) data for a range of years.
3. Extract atmospheric deposition (tDEP) data for a range of years.
4. Extract a dominant-component soil profile from a gSSURGO geodatabase using the `ameriflux-surgo-grid-extract` skill.

The result is a single JSON file containing all extracted information.

## Implementation Details
- Uses the vision extraction logic from `.agents/skills/ameriflux-site-info`.
- Reuses NADP and tDEP extraction code from `.agents/skills/ameriflux-atmchem-info`.
- Calls the gSSURGO extraction script (`extract_gssurgo_profile.py`) via subprocess to obtain soil profile data.
- Coordinates are transformed as needed for each data source.
- All data are merged under top‑level keys: `site_id`, `site_metadata`, `nadp`, `tdep`, and `gssurgo`.

## Prerequisites
- Python 3.8+.
- Install required packages:
  ```bash
  pip install playwright requests rasterio pyproj pyogrio geopandas numpy pandas netCDF4
  playwright install chromium
  ```
- Ollama must be running with the `qwen2.5vl:7b` model.
- Access to the gSSURGO geodatabase (`gSSURGO_CONUS.gdb`).

## Usage
```bash
python .agents/skills/unified-ameriflux-extractor/unified_ameriflux_extractor.py \
    --site-id US-Ha1 \
    --nadp-input /path/to/nadp_data \
    --tdep-input /path/to/tdep_data \
    --year1 2010 --year2 2020 \
    --gssurgo-gdb /path/to/gSSURGO_CONUS.gdb \
    --gssurgo-template /path/to/template.nc \
    --gssurgo-out result/US-Ha1/gssurgo_US-Ha1.json \
    --gssurgo-extend-last \
    --output result/US-Ha1/unified_output.json \
    --climate-output result/${site_id}/${site_id}_ecosim_climate.nc \
    --grid-output result/${site_id}/${site_id}_ecosim_grid.nc \
    --climate-data-dir data \
    --result-dir result
```
- `--site-id` is optional if latitude/longitude are provided directly, but required when generating EcoSIM climate or grid forcing files.
- If `--gssurgo-gdb`, `--gssurgo-template`, and `--gssurgo-out` are omitted, the gSSURGO extraction step is skipped.
- `--climate-output` (optional) specifies where to write the EcoSIM climate forcing NetCDF file. The script will invoke the climate forcing script located at `Tools/create_ecosim_climate_forcing.py`.
- `--grid-output` (optional) specifies where to write the EcoSIM grid forcing NetCDF file. The script will invoke the grid forcing script located at `Tools/create_ecosim_grid_forcing.py`.
- `--climate-data-dir` points to the directory containing ERA5 files (default: `data`).
- `--result-dir` is the directory for intermediate results (default: `result`).

The script will create the unified JSON output, generate any requested NetCDF forcing files, and print confirmation messages. Site-specific outputs should be placed under `result/<SITE_ID>/`.

When climate or grid NetCDF files are generated, the workflow should also emit derivation report JSON files that list template variables which could not be derived from source data and were left as fill/default values.

Climate NetCDF generation must apply range-aware gap filling:
- ERA5 meteorology values outside legitimate physical bounds are masked and filled by time interpolation before hourly aggregation.
- NADP chemistry values must be finite and non-negative, with `PHRG` constrained to pH 0-14.
- Annual chemistry gaps are filled by linear interpolation with nearest-edge filling.
- If `PHRG` cannot be derived from NADP data, write `PHRG=7` and record the policy fallback in the derivation report.

**Note:** `create_ecosim_climate_forcing.py` and `create_ecosim_grid_forcing.py` have been moved to the `Tools/` directory. All internal calls have been updated accordingly.
