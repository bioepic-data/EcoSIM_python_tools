# EcoSIM Soil Management Contract

Use this reference for exact soil-management file layout, Excel editing schema, and EcoSIM reader behavior. The reader is `f90src/IOutils/ReadManagementMod.F90`; the bundled bridge is `scripts/soil_mgmt_excel_bridge.py`.

## NetCDF Layout

Core dimensions:

```text
ntopou      number of topo units
year        number of year records
string10    10 chars for selector names
nfert       fertilizer records per fertilizer table, max 12 in the reader
string128   128 chars for fertilizer/irrigation event rows
ntill       tillage records per tillage table
string24    24 chars for tillage event rows
nirri       irrigation records per irrigation table, max 24 in the reader
```

Required variables:

```text
year(year)
NH1(ntopou)
NV1(ntopou)
NH2(ntopou)
NV2(ntopou)
fertf(year, ntopou, string10)
tillf(year, ntopou, string10)
irrigf(year, ntopou, string10)
```

Selector behavior:

```text
NO       no management of that type
<name>   read NetCDF variable named <name>
auto*    irrigation selector beginning with auto triggers automated irrigation parsing
```

The reader searches `year` for the forcing year (`yeari`). If no matching year exists, the shown reader loop has no explicit bound check, so files should cover every forcing year in the run.

## Fertilizer Rows

Fertilizer table variables are char arrays such as `fertf_2024(nfert, string128)`. The Fortran reader expects exactly 27 fields:

```text
DDMMYYYY
NH4Soil
NH3Soil
UreaSoil
NO3Soil
NH4Band
NH3Band
UreaBand
NO3Band
MonocalciumPhosphateSoil
MonocalciumPhosphateBand
hydroxyapatite
LimeStone
Gypsum
PlantResC
PlantResN
PlantResP
ManureC
ManureN
ManureP
AppDepth
BandWidth
PO4Soil
PO4Band
IsAmendtypFert
IsAmendtypResidual
IsAmendtypManure
```

Units and interpretation:

```text
N, P, C, Ca fields  g m-2
AppDepth            m
BandWidth           m
type flags          integer category flags
```

Useful conversion:

```text
1 g m-2 = 10 kg ha-1
```

The reader assigns these fields directly to `FERT(...)`, `FDPTH`, `ROWI`, and `IYTYP`.

## Tillage Rows

Tillage variables are char arrays such as `tillf_2024(ntill, string24)`. Each row has:

```text
DDMMYYYY
iSoilDisturbType
DepzCorp
```

Reader meaning:

```text
iSoilDisturbType  1-20 tillage, 21 litter removal, 22 fire, 23-24 drainage
DepzCorp          intensity for fire or depth for tillage/drainage
```

## Irrigation Rows

Scheduled irrigation variables are char arrays such as `irrigf_2024(nirri, string128)`. Each scheduled row has:

```text
DDMMYYYY
RR
JST
JEN
WDPTH
PHQ
NH4
NO3
H2PO4
Al
Fe
Ca
Mg
Na
K
SO4
Cl
```

Reader meaning:

```text
RR       irrigation amount, mm over JST-JEN; reader converts to m h-1
JST/JEN  start/end hours
WDPTH    depth of irrigation application, m
PHQ      pH
ions     g m-3 in irrigation water; reader converts to molar concentration
```

Automated irrigation is used when the selector begins with `auto`. The first row of the referenced variable has:

```text
DST
DEN
iIrrigOpt
FIRRA
CIRRA
DIRRA
WDPTH
PHQ
NH4
NO3
H2PO4
Al
Fe
Ca
Mg
Na
K
SO4
Cl
```

## Excel Editing Schema

Use `scripts/soil_mgmt_excel_bridge.py` to round-trip NetCDF, Excel, and JSON. The workbook has seven sheets:

```text
control
topo_units
year_selectors
event_files
fertilizer
tillage
irrigation
```

`control` columns:

```text
key
value
```

`topo_units` columns:

```text
topou
NH1
NV1
NH2
NV2
```

`year_selectors` columns:

```text
year
topou
fertf
tillf
irrigf
```

`event_files` columns:

```text
category
file
```

Use `category` values `fertilizer`, `tillage`, or `irrigation`. This sheet preserves event-table variables even when they currently have no rows, such as dormant `fertf_test` or `tillf_test` variables.

`fertilizer` columns:

```text
file
event_index
DDMMYYYY
NH4Soil
NH3Soil
UreaSoil
NO3Soil
NH4Band
NH3Band
UreaBand
NO3Band
MonocalciumPhosphateSoil
MonocalciumPhosphateBand
hydroxyapatite
LimeStone
Gypsum
PlantResC
PlantResN
PlantResP
ManureC
ManureN
ManureP
AppDepth
BandWidth
PO4Soil
PO4Band
IsAmendtypFert
IsAmendtypResidual
IsAmendtypManure
```

`tillage` columns:

```text
file
event_index
DDMMYYYY
iSoilDisturbType
DepzCorp
```

`irrigation` columns:

```text
file
event_index
mode
DDMMYYYY
DST
DEN
RR
JST
JEN
iIrrigOpt
FIRRA
CIRRA
DIRRA
WDPTH
PHQ
NH4
NO3
H2PO4
Al
Fe
Ca
Mg
Na
K
SO4
Cl
```

Use `mode=scheduled` for `DDMMYYYY/RR/JST/JEN` rows and `mode=auto` for `DST/DEN/iIrrigOpt/FIRRA/CIRRA/DIRRA` rows.

Common commands:

```bash
.venv-cmip6/bin/python .agents/skills/ecosim-soil-mgmt/scripts/soil_mgmt_excel_bridge.py inspect input.nc
.venv-cmip6/bin/python .agents/skills/ecosim-soil-mgmt/scripts/soil_mgmt_excel_bridge.py nc-to-xlsx input.nc editable.xlsx
.venv-cmip6/bin/python .agents/skills/ecosim-soil-mgmt/scripts/soil_mgmt_excel_bridge.py xlsx-to-json editable.xlsx edited.json
.venv-cmip6/bin/python .agents/skills/ecosim-soil-mgmt/scripts/soil_mgmt_excel_bridge.py xlsx-to-nc editable.xlsx edited.nc --json-output edited.json
.venv-cmip6/bin/python .agents/skills/ecosim-soil-mgmt/scripts/soil_mgmt_excel_bridge.py json-to-nc input.json output.nc
```

## Validation Notes

Check these before using the file in a run:

```text
selectors != NO point to existing variables
dates are valid DDMMYYYY
event date years match selector years unless deliberately yearless
annual N/P totals are plausible
no negative nutrient, depth, width, or irrigation values
record counts fit reader limits
```

The Fortran reader uses the event-string year for leap-year day-of-year conversion. A typo such as `07120090` will be treated as year 0090; it may land on the same day-of-year as the intended non-leap year, but it is still a data-quality issue.
