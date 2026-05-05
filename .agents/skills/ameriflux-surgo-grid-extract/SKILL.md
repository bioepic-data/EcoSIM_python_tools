---
name: ameriflux-surgo-grid-extract
description: Extract dominant-component gSSURGO soil profile variables for EcoSIM grid or template inputs. Use when deriving soil depth, bulk density, field capacity, wilting point, hydraulic conductivity, texture, rock fraction, pH, CEC, or soil organic carbon from gSSURGO.
---

# AmeriFlux gSSURGO Grid Extractor

## Use When

- You need soil profile values for an AmeriFlux or EcoSIM site from a local gSSURGO geodatabase.
- You need EcoSIM template variables such as `CDPTH`, `BKDSI`, `FC`, `WP`, `SCNV`, `SCNH`, `CSAND`, `CSILT`, `ROCK`, `PH`, `CEC`, or `CORGC`.
- You need depth-weighted interpolation from gSSURGO horizons to EcoSIM soil layers.

## Constraints
- NEVER use it extract climate data.

## Workflow

1. Locate `gSSURGO_CONUS.gdb` under `data/` first, then elsewhere in the repo if needed.
2. Identify the map unit (`MUKEY`) by spatial query on `MUPOLYGON`.
3. Select the dominant component by `comppct_r`.
4. Retrieve horizons and rock fragments from `chorizon` and `chfrags`.
5. Convert units and interpolate vertically to the target template layers.
6. Write the derived soil profile JSON under `result/<SITE_ID>/`.

## Overview

This document summarizes which variables in the provided template can be
extracted from the CONUS gSSURGO database (directory `gSSURGO_CONUS.gdb`), along
with methods for extraction and vertical interpolation.

## Extractable Variables from gSSURGO

The following template variables can be derived from standard gSSURGO
tables:

  ---------------------------------------------------------------------------
  Template Variable               gSSURGO Source               Notes
  ------------------------------- ---------------------------- --------------
  CDPTH                           chorizon.hzdepb_r / 100      Depth to
                                                               bottom of
                                                               horizon (m)

  BKDSI                           chorizon.dbovendry_r         Bulk density
                                                               (g/cm³)

  FC                              (wthirdbar_r / 100) \*       Field capacity
                                  dbthirdbar_r                 (volumetric)

  WP                              (wfifteenbar_r / 100) \*     Wilting point
                                  dbfifteenbar_r               

  SCNV, SCNH                      ksat_r \* 3.6                Convert µm/s
                                                               to mm/h

  CSAND                           sandtotal_r \* 10            g/kg

  CSILT                           silttotal_r \* 10            g/kg

  ROCK                            sum(chfrags.fragvol_r) / 100 Volume
                                                               fraction

  PH                              ph1to1h2o_r                  Soil pH

  CEC                             cec7_r                       Cation
                                                               exchange
                                                               capacity

  CORGC                           om_r \* 0.58 \* 10           Soil organic
                                                               carbon
  ---------------------------------------------------------------------------

## Non-Extractable Variables

The following variables are not directly available from gSSURGO and
require external datasets or modeling assumptions:

-   Climate variables (e.g., ATCAG)
-   Topography (e.g., ASPX, slope)
-   Hydrologic boundary conditions
-   Nutrient pools (NH4, NO3, PO4)
-   Organic nitrogen/phosphorus pools
-   Exchange coefficients (GKC\*)
-   Water table dynamics

## Extraction Workflow

1.  Identify MUKEY using spatial query on MUPOLYGON.
2.  Select dominant component using comppct_r.
3.  Retrieve horizons from chorizon.
4.  Join rock fragment data from chfrags.
5.  Compute derived variables.

## Vertical Interpolation

-   Use overlap-weighted averaging for most variables.

-   For soil organic matter (CORGC), apply logarithmic interpolation:

    log-interpolate values across depth, then exponentiate.

-   Optionally extend deepest horizon downward.

## Script

A Python script (`extract_gssurgo_profile.py`) is provided to
automate: - Spatial lookup - Horizon extraction - Variable conversion -
Vertical interpolation

## Example Usage
To execute the skill, run the following command from the project root. The resulting JSON will be saved to the `./result/` directory:

```bash
python .agents/skills/ameriflux-surgo-grid-extract/extract_gssurgo_profile.py \
  --gdb /path/to/gSSURGO_CONUS.gdb \
  --lon -121.85 \
  --lat 39.0 \
  --template template.nc \
  --out result/<SITE_ID>/profile_<SITE_ID>.json \
  --extend-last
```

## Notes

-   Bulk density and water retention conversions assume standard
    pedotransfer interpretations.
-   Ensure gSSURGO geodatabase includes required tables: MUPOLYGON,
    component, chorizon, chfrags.
