---
name: ecosim-natural-plant-mgmt
description: "Prepare EcoSIM plant management inputs for natural ecosystems using pft_mgmt_in JSON and NetCDF files. Use when creating or validating natural PFT plant management data, pft_type blocks, pft_pltinfo planting strings, monthly tree thinning events, or PlantMgmtWriter.py inputs for EcoSIM."
---

# EcoSIM Natural Plant Management

## Overview

Use this skill to build EcoSIM `pft_mgmt_in` inputs for natural ecosystems. Natural PFTs normally need only planting information; tree PFTs also receive an annual 1% thinning rate spread uniformly over 12 monthly events.

Read `references/plant_mgmt_contract.md` when you need exact NetCDF dimensions, variable names, string formats, thinning event fields, or JSON examples.

## Workflow

1. Identify active PFTs for each topo unit and validate their EcoSIM vegetation codes with `$ecosim-vegetation-code` against `templates/ecosim_pftpar_20260303.nc.cdl`.
2. Use `pft_dflag = 0` for constant natural vegetation unless the user explicitly needs transient yearly PFT composition. With `pft_dflag = 0`, include one year record such as `2000`; EcoSIM uses record 1.
3. Set each topo unit `NZ` to the active PFT count. Do not exceed `maxpfts = 5`; only the first `NZ` PFT entries matter.
4. For each PFT, set `pft_type` to the validated six-character EcoSIM code. EcoSIM will use the first four characters plus grid Koppen code when `KoppenClimZone_col > 0`, but keep the full validated code for clarity.
5. For planting, use `DDMMYYYY = "01019999"` unless the user provides a site-specific date. Derive `Planting_population` from web/literature evidence as plants or shoots per square meter, and derive `Planting_depth` in meters from species/PFT establishment information.
6. For non-tree natural PFTs, set `mgmt: []`.
7. For tree PFTs, add 12 monthly thinning events using `FractionCut = 0.01 / 12 = 0.0008333333`. Use no exported harvest fractions unless the user requests biomass removal from the ecosystem.
8. Write JSON first, then convert to NetCDF with the existing helper. Use a Python environment with `netCDF4` installed; in this repo `.venv-cmip6/bin/python` is known to work.

```bash
.venv-cmip6/bin/python applications/notebooks/scripts/PlantMgmtWriter.py input.json output.nc
```

If that helper is not present in the active repo, use:

```bash
python /Users/jinyuntang/work/github/ecosim_workspace/main/python_tools/applications/notebooks/scripts/PlantMgmtWriter.py input.json output.nc
```

## Evidence Rules

- Search the web or literature for typical density and planting depth when values are not provided. Cite sources in the response or derivation note.
- Prefer species-specific stand density, seedling density, stem density, tiller density, or plant density. Convert all density units to plants m-2.
- Avoid substituting percent cover, LAI, biomass, or seeding rate for plant density unless no better source exists; if used, label it as an assumption.
- Convert depths to meters. If evidence is weak, use conservative defaults only with an explicit note: herbaceous PFTs often need shallow depths, tree seedlings need a larger initial depth.

## Tree Thinning Convention

Apply monthly thinning only to tree PFTs such as `ndlf`, `ndld`, `bdlf`, `bdln`, `bdlw`, `bspr`, `dfir`, `jpin`, `lpin`, `tasp`, and `woak`. Treat `bush`, `busn`, and `shru` as non-tree woody PFTs unless the user asks to include woody shrub thinning.

Use these monthly event dates with year `0000`:

```text
31010000 28020000 31030000 30040000 31050000 30060000
31070000 31080000 30090000 31100000 30110000 31120000
```

Each thinning event should use:

```json
{
  "iHarvType": 0,
  "jHarvType": 0,
  "CutHeight": 1000.0,
  "FractionCut": 0.0008333333,
  "FineFractionLeafHarvested_pft": 1,
  "FineFractionNonleafHarvested_pft": 1,
  "StalkFractionHarvested_pft": 1,
  "StandeadFractionHarvested_pft": 0,
  "FineFractionLeafHarvested_col": 0,
  "FineFractionNonleafHarvested_col": 0,
  "StalkFractionHarvested_col": 0,
  "StandeadFractionHarvested_col": 0
}
```

This represents natural mortality/thinning without ecosystem biomass export. Flag the mass-flow assumption if changing ecosystem-level export fractions.

## Validation

Run the writer and check:

```bash
.venv-cmip6/bin/python applications/notebooks/scripts/PlantMgmtWriter.py input.json output.nc
ncdump -h output.nc
```

Verify that `pft_dflag`, `year`, `NH1/NV1/NH2/NV2/NZ`, `pft_type`, `pft_pltinfo`, `nmgnts`, and `pft_mgmt` exist; `NZ` equals active PFT count; non-tree PFTs have zero management events; tree PFTs have 12 events.
