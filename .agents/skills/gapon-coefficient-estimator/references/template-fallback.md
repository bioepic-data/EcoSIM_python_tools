# Ecosystem-Template Fallback

## Purpose

The bundled cases provide depth-explicit starting values for EcoSIM when paired
exchange-phase and solution-phase chemistry is unavailable. They are
initialization templates, not measurements for the target site and not a
replacement for calibration.

The copied source cases are stored under
`assets/ecosystem_templates/`. `template_catalog.csv` indexes one row per soil
profile, including ecosystem, climate, vegetation, water regime, management,
region, and source-file provenance.

## Selection Order

1. Match ecosystem family: cropland, forest, pasture, grassland, tundra,
   wetland, peatland, or rainforest.
2. Refine by climate.
3. Refine by dominant species, vegetation type, or crop rotation.
4. Refine by water regime and management, especially dryland versus irrigated
   agriculture.
5. Prefer the case default only as a final tie-breaker.

Automatic matching must not cross ecosystem families just because climate is
similar. If no same-family case exists, choose an explicit `--template-id`,
record why it is ecologically closest, and retain the low-confidence warning.

## Depth Mapping

Source layers are retained when target depths are not supplied. For requested
EcoSIM layer-bottom depths, the selector assigns the source layer containing
each target bottom depth. A target below the deepest source layer receives the
deepest source value and is marked through the provenance depth map.

The current source profiles generally repeat coefficients by depth, but their
layer structure is intentionally preserved. This keeps output depth-explicit
and allows future horizon-varying templates without changing the workflow.

## EcoSIM Mapping

| CSV field | EcoSIM field | Exchange pair |
|---|---|---|
| `gkc4` | `GKC4` | Ca-NH4 |
| `gkch` | `GKCH` | Ca-H |
| `gkca` | `GKCA` | Ca-Al |
| `gkcm` | `GKCM` | Ca-Mg |
| `gkcn` | `GKCN` | Ca-Na |
| `gkck` | `GKCK` | Ca-K |

Transfer the six fields as a set. Do not silently combine coefficients from
different templates.

## Required Provenance

The selector writes `gapon_source_method=ecosystem_template_fallback`, the
template ID, source case, source soil profile, source layer, source depth, and
`qc_flags=template_based;subject_to_tuning`. Keep the generated provenance JSON
with any Excel, JSON, or NetCDF input derived from it. Add equivalent global
attributes or report fields when the destination format supports them.

Always state:

> Gapon coefficients are initialized from the closest ecosystem template, not
> derived from site-specific paired exchange and solution chemistry. They are
> starting values and are subject to calibration or tuning when needed.

Paired chemistry supersedes the template. Useful tuning constraints include
exchangeable-cation composition, soil-solution cations, pH and sodicity,
nutrient response, leaching, and cation mass balance.
