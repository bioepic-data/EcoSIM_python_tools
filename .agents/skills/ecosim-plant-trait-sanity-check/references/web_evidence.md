# Web Evidence Workflow

Use web evidence to catch ecologically implausible parameters that cannot be judged from file structure alone. Every web-informed finding should be traceable to a source URL, evidence level, and unit conversion note.

## Source Priority

Use sources in this order:

1. Species-specific peer-reviewed papers, government plant guides, or curated species profiles for identity, life form, photosynthetic pathway, phenology, rooting habit, nitrogen fixation, and plant architecture.
2. Trait databases with standardized units and attribution, especially TRY, BIEN, LEDA, ORNL DAAC photosynthesis datasets, LeafWeb, and Global Spectra-Trait Initiative data.
3. Genus-, family-, or plant-functional-type syntheses when species evidence is missing.
4. Extension, restoration, or botanical garden summaries only as supporting evidence.

Useful starting points:

- TRY Data Portal: https://www.try-db.org/TryWeb/Database.php
- Global Spectrum of Plant Form and Function dataset: https://doi.org/10.17871/TRY.81
- BIEN trait access documentation: https://rdrr.io/cran/BIEN/f/inst/doc/BIEN_tutorial.Rmd
- LEDA Traitbase: https://uol.de/en/landeco/research/leda
- ORNL DAAC global photosynthesis and leaf trait dataset: https://doi.org/10.3334/ORNLDAAC/1224
- LeafWeb: https://www.leafweb.org/information/about/
- Global Spectra-Trait Initiative: https://doi.org/10.15485/2530733
- USDA PLANTS and NRCS Plant Guides for US species profiles: https://plants.usda.gov/

## Search Pattern

For each selected first-grid plant block:

1. Record the EcoSIM code, `NZ`, plant name, and any known site species.
2. Resolve the likely accepted scientific name. If the block is generic, such as `C3 grass perennial`, keep the evidence level as `functional-type`.
3. Search targeted terms:
   - `<taxon> leaf nitrogen phosphorus concentration`
   - `<taxon> Vcmax Jmax`
   - `<taxon> rooting depth root traits`
   - `<taxon> photosynthetic pathway`
   - `<taxon> phenology evergreen deciduous annual perennial`
4. Prefer sources with measurement units, sample size, geography, and citation.
5. Convert only traits that can be defensibly mapped to EcoSIM variables.

For annual plants, do not add a web-evidence expectation that `IWTYP` should be deciduous even when a botanical source describes the foliage that way. EcoSIM treats all annual plants as evergreen in the phenology-type field.

Do not add `SLA1` numeric ranges to web evidence, and do not use `SLA1` to derive leaf-area photosynthetic capacities for sanity-check findings. For photosynthetic properties, treat `CHL` as the fraction of total leaf protein in chlorophyll-bound/light-harvesting proteins, including chlorophyll-protein complexes associated with PSI, PSII, and LHC.

## Unit Conversion Notes

EcoSIM units often differ from trait database units. Document every conversion in `conversion_note`.

- `CNLF` is `gN gC-1`. If a source gives leaf N as `mg gDM-1`, convert with `CNLF = (leaf_N_mg_gDM / 1000) / carbon_fraction`.
- `CPLF` is `gP gC-1`. If a source gives leaf P as `mg gDM-1`, convert with `CPLF = (leaf_P_mg_gDM / 1000) / carbon_fraction`.
- `GRDM` is seed carbon mass in `gC seed-1`. Convert dry seed mass with `GRDM = seed_mass_gDM * carbon_fraction`.
- `PEPC` is the fraction of total leaf protein C allocated to PEPC, while `CNWL` is total leaf protein C per unit total leaf N. If a source reports the fraction of total leaf N allocated to PEPC, map it with `PEPC = fN_PEPC * protein_C_to_N / CNWL`. Use a measured protein C:N ratio when available; otherwise document the screening assumption of `3.3 gC gN-1`. Conversely, the checker estimates `fN_PEPC = PEPC * CNWL / 3.3` for C4 blocks.
- Map Rubisco nitrogen allocation in the same way: `RUBP = fN_Rubisco * protein_C_to_N / CNWL`. Do not judge `RUBP` or `PEPC` independently of `CNWL`.
- When a source reports leaf-area `Vpmax:Vcmax` or `Jmax:Vcmax`, compare it to the corresponding protein-normalized EcoSIM ratio only as a screening constraint. Record the source growth stage and temperature normalization; do not present the ratio as a direct unit conversion.
- Evaluate `VCMX`, `VOMX`, `XKCO2`, and `XKO2` as one kinetic set. Preserve both a plausible carboxylation:oxygenation turnover ratio and a plausible implied specificity; matching specificity alone does not make compensating Km and turnover values physiological.
- Web `Vcmax25` is commonly leaf-area based (`umol m-2 s-1`), while EcoSIM `VCMX` is Rubisco-C based (`umol CO2 (gC rubisco)-1 s-1`). Do not compare these directly unless the conversion is explicitly supported by additional Rubisco or leaf carbon information.

## Evidence JSON

Save web evidence as JSON and pass it to the checker with `--web-evidence`. Numeric ranges must already be in EcoSIM units.

```json
{
  "plants": [
    {
      "pft_code": "ndlf35",
      "nz": 1,
      "ny": 1,
      "nx": 1,
      "taxon": "generic evergreen needleleaf tree",
      "numeric_ranges": [
        {
          "variable": "RUBP",
          "min": 0.05,
          "max": 0.35,
          "unit": "gC rubisco gC protein-1",
          "source": "functional-type protein-allocation synthesis",
          "url": "https://www.try-db.org/TryWeb/Database.php",
          "evidence_level": "functional-type",
          "conversion_note": "Range must match EcoSIM's total-leaf-protein basis."
        }
      ],
      "categorical_expectations": [
        {
          "variable": "ICTYP",
          "contains": "C3",
          "source": "functional-type identity",
          "url": "https://www.try-db.org/TryWeb/Database.php",
          "evidence_level": "functional-type"
        }
      ]
    }
  ]
}
```

## Interpretation

Web evidence is contextual, not absolute. Treat species-level, measured, site-relevant evidence as strongest. Treat global trait-database summaries and plant-functional-type ranges as screening ranges that should generate warnings, not automatic edits.
