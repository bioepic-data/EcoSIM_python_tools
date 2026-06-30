# Data Requirements for Gapon Coefficient Estimation

## Minimum paired data

For each horizon, layer, or sample:

- `exchange_ca_cmolc_kg` plus one or more target exchangeable cations:
  `exchange_na_cmolc_kg`, `exchange_mg_cmolc_kg`,
  `exchange_k_cmolc_kg`, `exchange_nh4_cmolc_kg`,
  `exchange_al_cmolc_kg`, `exchange_fe_cmolc_kg`,
  `exchange_h_cmolc_kg`.
- `activity_ca` plus the matching solution activity columns:
  `activity_na`, `activity_mg`, `activity_k`, `activity_nh4`,
  `activity_al`, `activity_fe`, `activity_h`.

If activities are unavailable, use consistently normalized solution
concentration columns such as `solution_ca_mol_l` or `solution_ca_mmol_l`, but
flag the result as concentration-as-activity.

## Lyotropic adsorption series

Use the cation adsorption series `Al = Fe > Ca > Mg > K = NH4` as a
scientific prior and sanity check. For EcoSIM, this means:

- `Al` and `Fe` should generally be the strongest exchange competitors.
- `Ca` should be preferred over `Mg`, and `Mg` over `K` and `NH4`.
- `K` and `NH4` should usually be treated as similar-strength competitors.
- `Na` remains useful for sodicity and Ca-Na exchange, but it is outside this
  specific series.
- `H` is governed by pH and acidity conventions; do not force it into the
  base-cation adsorption order.

If paired data imply a different order, do not silently adjust the
coefficients. Report the inversion and first check unit conversions,
extraction methods, activity corrections, and Fe/Al speciation.

## Common SSURGO/gSSURGO columns

Useful priors:

- `cec7_r`: CEC at pH 7, cmolc/kg
- `ecec_r`: effective CEC, cmolc/kg
- `sumbases_r`: sum of bases, cmolc/kg
- `ph1to1h2o_r`: pH in 1:1 water
- `ec_r`: electrical conductivity
- `sar_r`: sodium adsorption ratio
- `extracid_r`: extractable acidity, cmolc/kg
- `extral_r`: extractable aluminum, cmolc/kg

Standard SSURGO `chorizon` does not provide all individual exchangeable
`Ca`, `Mg`, `Na`, `K`, `NH4`, `Al`, and `Fe` needed to isolate Gapon solid
ratios. Do not treat non-standard names such as `extrca_r`, `extrmg_r`,
`extrna_r`, `extrk_r`, or `extrfe_r` as guaranteed SSURGO columns without
checking the actual dataset.

## CaX closure assumptions

Only use closure when `exchange_ca_cmolc_kg` is missing and enough companion
exchange cations are present.

Neutral/non-acidic approximation:

`CaX = CEC7 - (MgX + NaX + KX + NH4X + FeX_known)`

Acidic approximation:

`CaX = ECEC - (MgX + NaX + KX + NH4X + AlX + FeX + HX)`

If only exchangeable acidity and Al are known:

`HX = max(exchange_acidity - AlX, 0)`

Do not infer `FeX` from total Fe, citrate-dithionite Fe, oxalate Fe, or
generic extractable Fe unless the analytical method is explicitly an
exchangeable Fe measurement in charge-equivalent units.

All closures are estimates and must be reported in QC.

## Global database suitability

- WoSIS: best global profile backbone, partial support depending on profile
  measurements; still often lacks complete paired exchange and solution data.
- SoilGrids: useful for spatial priors such as pH, CEC, texture, SOC, and bulk
  density; not enough for direct Gapon coefficient calculation.
- HWSD/WISE/GSDE: useful for coarse priors such as pH, CEC, base saturation,
  total exchangeable bases, and salinity/sodicity screening; not enough for
  direct coefficient calculation.
- Water-quality datasets such as GEMStat or GLORICH can help with regional
  solution chemistry, but they are not soil exchange datasets and need careful
  spatial/depth interpretation.
