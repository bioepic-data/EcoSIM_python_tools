---
name: ecosim-plant-trait-sanity-check
description: Sanity-check EcoSIM plant_trait.*.desc parameter values for the first grid only. Use when validating plant trait description files, reviewing one-plant-per-block trait records, or checking ranges, units, and woody/herbaceous block consistency before running EcoSIM.
---

# EcoSIM Plant Trait Sanity Check

## Overview

Use this skill to sanity-check EcoSIM `plant_trait.*.desc` files. Each `PLANT traits for FUNCTIONAL TYPE` block represents one plant, and the default check is intentionally confined to the first grid only: `NY=1, NX=1`. All active plant blocks at that grid are checked.

The check has two layers:

- deterministic file checks for malformed values, units, ranges, and block consistency
- web-informed ecological checks using species, genus, or plant-functional-type evidence gathered during the task

## Workflow

1. Locate the target `plant_trait.*.desc` file. If the user gives no path, prefer a local path they recently mentioned, then search under `data/`, then under the repository.
2. Run the deterministic checker script on the file:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc
```

3. Keep the default grid scope unless the user explicitly asks for another grid. The default is equivalent to:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc --ny 1 --nx 1
```

4. Use web search to gather trait evidence for each first-grid plant block. Read [references/web_evidence.md](references/web_evidence.md), then search for the plant name, likely taxon, or functional type plus trait terms.
5. Convert the evidence into EcoSIM units and save a temporary evidence JSON file. Use species-level evidence when available; otherwise use genus, family, or functional-type evidence and mark that evidence level.
6. Re-run the checker with the evidence file:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc --web-evidence /absolute/path/to/web_evidence.json
```

7. Report findings by severity. Lead with `ERROR` findings, then `WARN` findings, and include the plant code, grid tuple, parameter name, source line, and web source when applicable.
8. If there are no findings, state that the first-grid plant blocks passed both deterministic and web-informed checks and mention how many plants and parameters were inspected.

## What Is Checked

The checker validates the plant blocks at the selected grid for:

- required EcoSIM trait sections
- parseable finite numeric values in numeric sections
- fraction variables within `[0, 1]`
- positive rates, capacities, dimensions, uptake parameters, resistance terms, and nutrient ratios
- `CLASS` as four inclination fractions that sum to one
- optical albedo plus transmission not exceeding one
- osmotic potential sign and standing dead biomass sign
- growth yield bounds
- N and P concentration magnitudes
- class-information conventions, including that annual plants are treated as evergreen in EcoSIM
- woody versus herbaceous root trait consistency
- simple cross-parameter checks such as `PhiMIN <= PhiMAX` and fine-root radius not exceeding primary-root radius

Read [references/sanity_rules.md](references/sanity_rules.md) before expanding the checker or interpreting a borderline warning. Read [references/web_evidence.md](references/web_evidence.md) before making web-informed trait comparisons.

## Web-Informed Evidence

The script does not browse by itself. Codex must do the web search, evaluate sources, convert values into EcoSIM units, and provide the evidence as JSON. This keeps the check reproducible and prevents untraceable web-derived warnings.

Use this JSON shape:

```json
{
  "plants": [
    {
      "pft_code": "woat35",
      "nz": 3,
      "ny": 1,
      "nx": 1,
      "taxon": "Avena fatua",
      "numeric_ranges": [
        {
          "variable": "RUBP",
          "min": 0.05,
          "max": 0.35,
          "unit": "gC rubisco gC protein-1",
          "source": "literature-derived protein-allocation range",
          "url": "https://example.org/source",
          "evidence_level": "species",
          "conversion_note": "Range must match EcoSIM's total-leaf-protein basis."
        }
      ],
      "categorical_expectations": [
        {
          "variable": "ICTYP",
          "contains": "C3",
          "source": "USDA/NRCS or species profile",
          "url": "https://example.org/source",
          "evidence_level": "species"
        }
      ]
    }
  ]
}
```

Web evidence findings default to `WARN` because literature and trait database ranges vary with species, site, phenology, and measurement protocol. Use `severity: "ERROR"` in the evidence JSON only when a value is unequivocally impossible or contradicts a required categorical identity. Do not use external deciduous foliage descriptions to override the EcoSIM convention that annual plants are represented as evergreen in `IWTYP`.

For photosynthetic-property checks, interpret `CHL` as the fraction of total leaf protein in chlorophyll-bound/light-harvesting proteins, including chlorophyll-protein complexes associated with PSI, PSII, and LHC. Do not use `SLA1` values, or any `SLA1`-derived leaf-area capacity calculations, as part of the sanity check.

## Parser Notes

The parser treats each block header as a plant identity record:

```text
PLANT traits for FUNCTIONAL TYPE (NZ,NY,NX)= <NZ> <NY> <NX> <pft_code>
```

Parameter names are not globally unique. For example, `KLGMAX` can appear twice in woody root sections with different meanings, so preserve file order and section context when discussing findings.

Trait descriptions sometimes contain colons, such as `Leaf length:width ratio`; split parameter values at the final colon in a row.

## Output Options

Use Markdown output for human review:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc
```

Use JSON output for automated pipelines:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc --json
```

Use web evidence in either Markdown or JSON mode:

```bash
python3 .agents/skills/ecosim-plant-trait-sanity-check/scripts/check_plant_trait_desc.py /absolute/path/to/plant_trait.1930.desc --web-evidence /absolute/path/to/web_evidence.json --json
```

The script returns a nonzero status when `ERROR` findings are present or when no blocks match the requested grid.

## Reporting Guidance

Do not edit the trait file unless the user asks for corrections. This skill is a diagnostic pass.

When summarizing results, make clear that the check is scoped to the first grid by default, not the full file. If repeated grid columns exist, say how many total blocks were present and how many first-grid plant blocks were inspected.
