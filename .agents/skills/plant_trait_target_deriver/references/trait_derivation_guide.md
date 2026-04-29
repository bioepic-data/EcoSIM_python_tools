# Trait Derivation Guide

Use this guide when deriving a compact species trait summary for a named plant.

## Recommended source hierarchy

### Identity and growth form

- [Plants of the World Online](https://powo.science.kew.org/?locale=en_US)
- USDA species pages or equivalent official species profiles

Use these to resolve:

- accepted scientific name
- family
- woody vs herbaceous form
- annual vs perennial habit

### General ecology and crop constraints

- [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/en)
- USDA crop or forestry pages
- US Forest Service species syntheses
- FEIS species reviews

Useful for:

- climate envelope
- phenology
- growth habit
- rooting tendency
- canopy characteristics

### Trait databases and literature

- [TRY Plant Trait Database](https://www.try-db.org/TryWeb/Home.php/RegStart.php)
- peer-reviewed species, genus, or functional-type studies

Useful for:

- SLA
- nitrogen concentrations
- photosynthetic parameters
- root:shoot allocation

## Trait-by-trait recommendations

### Annual GPP

Preferred evidence:

- flux tower studies in stands dominated by the target species
- crop productivity papers
- ecosystem carbon balance papers

Fallback:

- functional-type-level range with strong caveat

### LAI

Preferred evidence:

- field observations
- crop manuals
- canopy structure papers
- flux metadata if clearly species-relevant

### Specific LAI / SLA

Preferred evidence:

- trait databases
- leaf economics studies
- species physiology papers

Interpretation:

- default to specific leaf area unless the user specifies a different meaning
- final preferred unit for EcoSIM-facing output: `m2 gC-1`
- when literature reports dry-mass SLA, convert to `m2 gC-1` only if leaf carbon fraction is given or can be justified from the same source or a tightly matched source

### Vcmax25 and Jmax25

Preferred evidence:

- peer-reviewed gas exchange studies
- trait compilations reporting standardized values at 25oC

Avoid:

- rough conversions from unrelated temperatures without a cited method

### Root-to-shoot ratio

Preferred evidence:

- biomass partitioning studies
- forestry allometry papers
- crop allocation studies

### Rooting depth

Preferred evidence:

- crop handbooks
- forestry or root ecology papers
- species reviews

### Leaf protein nitrogen

Preferred evidence:

- leaf biochemistry or nitrogen allocation studies

Avoid:

- substituting total leaf nitrogen unless clearly noted as a proxy

### Leaf chlorophyll nitrogen

Preferred evidence:

- chlorophyll-N allocation studies
- papers partitioning photosynthetic nitrogen pools

Avoid:

- inferring from total chlorophyll alone unless the paper gives a supported relationship

## Provenance labels

Use one of:

- `species-sourced`
- `genus-inferred`
- `functional-type-inferred`
- `no-defensible-estimate`

## Minimal final note

When values come from mixed evidence, say so directly:

`This summary combines species-level measurements where available with genus- or functional-type inference for sparse traits.`
