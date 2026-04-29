# Trait Output Schema

Use this JSON shape when the user asks for machine-readable output.

```json
{
  "plant_name": "Limber Pine",
  "accepted_scientific_name": "Pinus flexilis",
  "growth_form": "tree",
  "traits": [
    {
      "trait": "annual_GPP",
      "value": 1200,
      "units": "gC m-2 yr-1",
      "provenance": "species-sourced",
      "source_links": [
        "https://example.org/paper"
      ],
      "notes": "Typical mature-stand value from species-dominated site."
    }
  ]
}
```

## Canonical trait keys

- `annual_GPP`
- `LAI`
- `specific_leaf_area`
  - preferred units: `m2 gC-1`
- `Vcmax25`
- `Jmax25`
- `root_to_shoot_ratio`
- `rooting_depth`
- `leaf_protein_nitrogen`
- `leaf_chlorophyll_nitrogen`
