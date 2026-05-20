# EcoSIM Plant Management Contract

Use this reference for exact file layout and natural-ecosystem conventions. The reader is `f90src/IOutils/PlantInfoMod.F90`; harvest type constants are in `f90src/Modelconfig/ElmIDMod.F90`; the preferred JSON-to-NetCDF helper is `applications/notebooks/scripts/PlantMgmtWriter.py`.

## NetCDF Layout

Required dimensions:

```text
ntopou      number of topo units
year        number of year records
maxpfts     5 active/possible PFT slots
maxpmgt     24 management events per PFT per year
nchar1      10 chars for pft_type
ncharmgnt   128 chars for planting/management strings
```

Required variables:

```text
pft_dflag
year(year)              required when pft_dflag /= 0; harmless for constant data
NH1(ntopou)
NV1(ntopou)
NH2(ntopou)
NV2(ntopou)
NZ(ntopou)
pft_type(year, ntopou, maxpfts, nchar1)
pft_pltinfo(year, ntopou, maxpfts, ncharmgnt)
nmgnts(year, ntopou, maxpfts)
pft_mgmt(year, ntopou, maxpfts, maxpmgt, ncharmgnt)  required if any nmgnts > 0
```

`pft_dflag` behavior:

```text
-1  no PFT data
 0  constant PFT data; reader uses record 1
 1  transient PFT data; reader matches yeari, the forcing year
other nonzero  reader matches yearc, the current model year
```

## String Formats

`pft_type` is read for each active PFT. If `KoppenClimZone_col > 0`, EcoSIM replaces the suffix with the grid Koppen code by using the first four chars plus the two-digit climate code. Keep six-character validated codes in JSON anyway.

Planting string:

```text
DDMMYYYY Planting_population Planting_depth
```

Natural ecosystem default:

```text
01019999 <plants_or_shoots_m-2> <depth_m>
```

Management event string:

```text
DDMMYYYY ICUT JCUT HCUT PCUT ECUT11 ECUT12 ECUT13 ECUT14 ECUT21 ECUT22 ECUT23 ECUT24
```

`ICUT` values:

```text
0 no touch
1 harvest grain
2 harvest shoot/all aboveground
3 pruning
4 grazing
5 fire
6 herbivory/animal grazing
```

`JCUT` values:

```text
0 no action
1 terminate plant
2 terminate and reseed
```

For `ICUT=4` or `ICUT=6`, the reader treats event pairs as grazing/herbivory start and end dates, filling the intervening days with the same settings. Do not use that pairing for the default tree thinning events.

## Natural Ecosystem JSON Pattern

Use this shape for `PlantMgmtWriter.py`:

```json
{
  "pft_dflag": 0,
  "years": [2000],
  "topo_units": [
    {
      "NH1": 1,
      "NV1": 1,
      "NH2": 1,
      "NV2": 1,
      "NZ": 2,
      "years": {
        "2000": {
          "pfts": [
            {
              "pft_type": "gr3a34",
              "planting": {
                "DDMMYYYY": "01019999",
                "Planting_population": 400,
                "Planting_depth": 0.005
              },
              "mgmt": []
            },
            {
              "pft_type": "woak31",
              "planting": {
                "DDMMYYYY": "01019999",
                "Planting_population": 0.05,
                "Planting_depth": 0.05
              },
              "mgmt": [
                {
                  "DDMMYYYY": "31010000",
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
              ]
            }
          ]
        }
      }
    }
  ]
}
```

Expand the tree `mgmt` list to all 12 monthly dates from `SKILL.md`. Keep non-tree PFT `mgmt` lists empty.

## Unit Conversions

Density must be plants or shoots per square meter:

```text
plants m-2 = plants ha-1 / 10000
plants m-2 = plants acre-1 / 4046.8564224
plants m-2 = plants ft-2 * 10.7639104
```

Planting depth must be meters:

```text
m = cm / 100
m = mm / 1000
m = inches * 0.0254
```

Document whether a density is individual plants, stems, seedlings, shoots, ramets, or tillers. For grasses and sedges, tiller/shoot density may be the best available proxy for EcoSIM plant population; note the proxy explicitly.
