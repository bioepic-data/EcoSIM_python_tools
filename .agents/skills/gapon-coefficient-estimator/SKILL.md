---
name: gapon-coefficient-estimator
description: Estimate calcium-normalized Gapon selectivity coefficients for soil cation exchange from paired exchange-phase and solution-phase cation data. Use when deriving EcoSIM exchange parameters such as Ca-Na, Ca-Mg, Ca-K, Ca-NH4, Ca-Al, or Ca-H Gapon coefficients; when checking whether SSURGO, gSSURGO, WoSIS, SoilGrids, HWSD, lab, saturated-paste, groundwater, or soil-solution data can support Gapon calculations; or when converting exchangeable cation and liquid ion datasets into coefficient tables with unit and mass-balance cautions.
---

# Gapon Coefficient Estimator

## Core Rule

Do not compute Gapon coefficients from SSURGO/gSSURGO alone. A defensible
calculation needs both:

- Exchange phase: exchangeable cations in charge-equivalent units, ideally
  `cmolc/kg` (`CaX`, `MgX`, `NaX`, `KX`, `NH4X`, `AlX`, `HX`).
- Solution phase: ion activities, or at least consistently unit-normalized
  dissolved concentrations for `Ca`, `Mg`, `Na`, `K`, `NH4`, `Al`, and `H`.

SSURGO/gSSURGO can provide priors such as `cec7_r`, `ecec_r`, `sumbases_r`,
`ph1to1h2o_r`, `ec_r`, `sar_r`, `extracid_r`, and `extral_r`, but standard
`chorizon` does not provide all species-resolved exchangeable bases or
solution cation activities.

## Preferred Workflow

1. Gather exchangeable cations from local lab data, WoSIS profiles, national
   soil lab datasets, or project measurements. Use SSURGO/gSSURGO only for
   CEC/ECEC/pH/acidity priors and gap flags.
2. Gather solution chemistry from saturated paste, soil solution, lysimeter,
   groundwater, stream chemistry, or a geochemical speciation model.
3. Convert exchangeable cations to consistent charge-equivalent units.
4. Convert solution concentrations to activities if possible. If using raw
   concentrations, label the output as an activity approximation.
5. Compute Ca-normalized Gapon coefficients with:

   `K_G(Ca-i) = (E_i / E_Ca) * a_Ca^(1/2) / a_i^(1/z_i)`

   where `E_i` and `E_Ca` are exchange-phase equivalent amounts and `z_i` is
   the cation charge. This gives exponents of 1 for monovalent ions, 1/2 for
   divalent ions, and 1/3 for Al3+.
6. Report quality flags: missing solution data, CaX closure assumptions,
   concentration-as-activity assumptions, negative closures, and conditional
   Ni/Co or Al/H interpretations.

## Important Scientific Cautions

- Ca-Mg under the general Gapon form uses `sqrt(a_Ca) / sqrt(a_Mg)`, not
  `a_Ca / a_Mg`. If a project uses Vanselow or Gaines-Thomas selectivity
  conventions, state that explicitly and do not mix coefficients.
- `extracid_r` is exchangeable acidity, not pure exchangeable H. If Al is
  separately available, estimate `HX = max(extracid - AlX, 0)` only as a
  flagged approximation.
- `extral_r` or lab-extractable Al is not automatically aqueous `Al3+`.
  Solution Al should be speciated because hydrolysis and DOC complexation
  strongly affect activity.
- `[H+] = 10^-pH` is a fallback activity estimate only; pH method and solution
  matrix matter.
- `NH4X` is transient and usually absent from regional soil maps; prefer local
  agronomic or incubation data.
- For EcoSIM, treat Gapon coefficients as calibrated uncertain parameters
  constrained by data, not deterministic outputs from global products.

## Script

Use `scripts/estimate_gapon_coefficients.py` for repeatable CSV calculations.
It accepts flexible column aliases, estimates missing `CaX` by a flagged CEC
or ECEC closure when requested, and writes coefficient plus QC columns.

Example:

```bash
python .agents/skills/gapon-coefficient-estimator/scripts/estimate_gapon_coefficients.py \
  --input data/site_exchange_solution.csv \
  --output result/site_gapon_coefficients.csv \
  --estimate-ca
```

Use `--self-test` to run a built-in smoke test.

## References

For column aliases, closure rules, and source-database suitability, read
`references/data-requirements.md` when the task involves unfamiliar data
schemas or global/national soil products.
