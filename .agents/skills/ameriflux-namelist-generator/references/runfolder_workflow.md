# AmeriFlux EcoSIM Run Folder Workflow

Use this workflow whenever a user asks to create a workable EcoSIM run folder, runfolder, run directory, or runnable case for a given AmeriFlux site. Assume the EcoSIM executable is already built unless the user says otherwise.

## Goal

Produce a run directory that contains or can resolve:

- an EcoSIM executable or symlink if the user wants it placed in the folder
- a site-specific `.namelist`
- reachable grid, climate, plant-management, PFT parameter, and greenhouse-gas NetCDF inputs
- optional output/log subdirectories

## Canonical Skill Order

1. Use `ameriflux-site-info` to resolve site metadata under `result/<SITE_ID>/`.
2. Use `ameriflux-atmchem-info` or `unified-ameriflux-extractor` to derive NADP/tDEP chemistry when climate chemistry variables are needed.
3. Use `ameriflux-surgo-grid-extract` or `unified-ameriflux-extractor` to derive soil/grid profile values.
4. Use `ameriflux-era5-to-ecosim` or `unified-ameriflux-extractor` to create hourly climate forcing.
5. Use `ecosim-vegetation-code` to validate the EcoSIM PFT code from site vegetation and Koppen code.
6. Use `ecosim-natural-plant-mgmt` to create `pft_mgmt_in` JSON and NetCDF.
7. Use `ameriflux-namelist-generator` to create the namelist and wire input paths into the run folder.

## Expected Artifacts

Prefer these paths:

```text
result/<SITE_ID>/<SITE_ID>_ecosim_site.json
result/<SITE_ID>/<SITE_ID>_ecosim_grid.nc
result/<SITE_ID>/<SITE_ID>_ecosim_climate.nc
result/<SITE_ID>/<SITE_ID>_pft_mgmt.json
result/<SITE_ID>/<SITE_ID>_pft_mgmt.nc
result/<SITE_ID>/<SITE_ID>_climate_derivation_report.json
result/<SITE_ID>/<SITE_ID>_grid_derivation_report.json
```

Use existing artifacts if they are current and plausible. Do not regenerate large inputs unless requested or clearly required.

## Run Folder Layout

Default to an EcoSIM-workspace layout when the user does not specify a directory:

```text
/Users/jinyuntang/work/github/ecosim_workspace/croots/examples/run_dir/<SITE_ID>/
  <SITE_ID>.namelist
  output/
```

If the executable should live in the run folder, symlink or copy it only when the user provides the executable path or it is obvious from the workspace. Otherwise leave the namelist ready and report the executable assumption.

## Namelist Creation

Generate the namelist from the Python-tools repository:

```bash
python .agents/skills/ameriflux-namelist-generator/scripts/create_ameriflux_namelist.py \
  --site-id <SITE_ID> \
  --output /Users/jinyuntang/work/github/ecosim_workspace/croots/examples/run_dir/<SITE_ID>/<SITE_ID>.namelist \
  --run-dir /Users/jinyuntang/work/github/ecosim_workspace/croots/examples/run_dir/<SITE_ID>
```

Use explicit overrides when needed:

- `--grid-file`
- `--pft-mgmt-file`
- `--climate-file`
- `--pft-file`
- `--atm-ghg-file`
- `--force-start-year`
- `--force-end-year`
- `--spinup-end-year`
- `--start-year`
- `--stop-n`

## Validation Checklist

Before declaring the folder workable:

1. Confirm the namelist exists.
2. From the run folder, resolve every namelist file path that is not `'NO'`.
3. Confirm `grid_file_in`, `pft_mgmt_in`, and `clm_hour_file_in` point to the intended site artifacts.
4. Confirm `forc_periods` uses climate forcing years that exist in the source ERA5 or climate NetCDF.
5. Confirm `delta_time=3600.` for hourly AmeriFlux/EcoSIM forcing.
6. Confirm `atm_ghg_in` spans the requested simulation period; historical GHGs through 2023 are not sufficient for future SSP runs.
7. Confirm `pft_mgmt_in` has active PFTs and reasonable planting density/depth units.
8. Confirm output frequency and `hist_fincl1` are appropriate for expected output volume.

## Scientific Cautions

- Do not set missing climate, grid, or plant-management inputs to `'NO'`; that can make the run physically meaningless.
- Treat gSSURGO/FAO fallback soil properties and NADP chemistry gap fills as assumptions; keep derivation reports with the run package.
- For natural vegetation, avoid mass-balance errors in management files: thinning without ecosystem export should use zero ecosystem-level harvested fractions.
- If forcing is recycled for spinup, document the repeated forcing window and cycle count.

## Completion Report

When finished, report:

- run folder path
- namelist path
- input files referenced by the namelist
- forcing year range and `stop_n`
- any missing assumptions, fallback data, or validation steps that could not be completed
