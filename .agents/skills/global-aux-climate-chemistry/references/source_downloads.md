# Source Downloads

Load this reference when a task requires concrete download commands, source selection, or source-to-variable mapping for non-US EcoSIM auxiliary precipitation chemistry.

## CAMS ADS

Use CAMS first for automated gridded wet-deposition chemistry outside the NADP domain.

Setup:

```bash
python -m pip install "cdsapi>=0.7.7"
```

ADS credentials can be stored in a CDSAPI config with:

```yaml
url: https://ads.atmosphere.copernicus.eu/api
key: <ADS_PERSONAL_ACCESS_TOKEN>
```

Use the CAMS dataset page's "Show API request code" panel for exact variable names. CAMS variable names are long and service-version dependent; never guess final names in production code.

Smoke-test pattern:

```python
import cdsapi

# Assumes ~/.cdsapirc is configured for ADS, or pass url/key explicitly
# with cdsapi.Client(url="https://ads.atmosphere.copernicus.eu/api", key="...").
client = cdsapi.Client()

dataset = "cams-global-atmospheric-composition-forecasts"
request = {
    "variable": [
        "total_precipitation",
        # Add exact wet-deposition variable names from ADS API request code:
        # ammonium aerosol wet deposition
        # fine/coarse nitrate aerosol wet deposition
        # sulphate aerosol wet deposition
        # sea-salt aerosol wet deposition
        # dust aerosol wet deposition
    ],
    "date": ["2024-01-01/2024-01-31"],
    "time": ["00:00"],
    "leadtime_hour": [str(hour) for hour in range(0, 24)],
    "type": ["forecast"],
    "data_format": "netcdf_zip",
    "area": [47.0, 6.0, 46.6, 6.4],
}

client.retrieve(dataset, request, "cams_deposition_smoke_test.zip")
```

After download:

1. Open the NetCDF/ZIP with `xarray`.
2. Print variable names, units, accumulation convention, dimensions, and time coverage.
3. Aggregate wet-deposition fluxes and precipitation over complete years only.
4. Divide annual wet-deposition flux by annual precipitation depth to produce precipitation concentration.

Expected EcoSIM mapping:

| EcoSIM variable | Preferred CAMS basis | Required check |
| --- | --- | --- |
| `CN4RIG` | ammonium wet deposition | compound vs elemental N |
| `CNORIG` | nitrate wet deposition, sum fine/coarse if both exist | compound vs elemental N |
| `CSORG` | sulphate wet deposition | compound vs elemental S |
| `CNARG`, `CCLRG` | sea-salt wet deposition approximation | low confidence unless species-specific Na/Cl available |
| `CCARG`, `CMGRG`, `CKARG` | dust/sea-salt approximations or station override | low confidence unless element-specific |
| `PHRG` | no default CAMS direct pH | prefer station pH or neutral default |

## EANET

Use EANET for East and Southeast Asian station wet-chemistry observations.

Download path:

- Open `https://monitoring.eanet.asia/document/public/index`.
- Download annual or monthly wet-deposition concentration files.
- Prefer wet concentration data for `PHRG`, `NH4`, `NO3`, `SO4`, `Ca`, `Mg`, `Na`, `K`, and `Cl` when columns exist.

Ingestion:

```python
import pandas as pd

df = pd.read_excel("eanet_wet_monthly_concentration.xlsx")
print(df.columns)
```

Always verify station coordinates, station type, units, missing-value codes, and whether values are concentration or deposition.

## EBAS

Use EBAS for European and other public station observations.

Access path:

- Open `https://ebas-data.nilu.no/`.
- Search by station, country, component, matrix, and time period.
- Export selected precipitation chemistry datasets.

Use EBAS primarily for station validation, pH, and base-cation overrides. Keep a copy of the export metadata with the EcoSIM derivation report.

## MERRA-2

Use MERRA-2 only as a fallback aerosol/deposition context source.

Suggested access through `earthaccess`:

```python
import earthaccess

earthaccess.login()

datasets = earthaccess.search_datasets(
    keyword="MERRA-2 aerosol diagnostics",
    daac="GES_DISC",
)
for dataset in datasets[:5]:
    print(dataset.summary())

results = earthaccess.search_data(
    short_name="<MERRA2_AEROSOL_COLLECTION_SHORT_NAME>",
    temporal=("2020-01-01", "2020-12-31"),
    bounding_box=(6.0, 46.6, 6.4, 47.0),
)
files = earthaccess.download(results, local_path="data/merra2")
```

Before using MERRA-2 in EcoSIM chemistry, inspect whether variables are wet deposition, dry deposition, burden, or surface concentration. Do not map MERRA-2 aerosol mass directly to precipitation chemistry without a documented deposition-to-concentration conversion.

## Output JSON Pattern

Prefer a source-neutral derivation JSON with one record per year:

```json
{
  "site_id": "Forbonnet-peatland",
  "lat": 46.8264,
  "lon": 6.1722,
  "source_priority": ["CAMS", "EBAS"],
  "data_by_year": {
    "2020": {
      "raw_ion_conc": {
        "ph": 5.2,
        "nh4_mg_l": 0.30,
        "no3_mg_l": 0.45,
        "so4_mg_l": 0.80,
        "ca_mg_l": 0.20,
        "mg_mg_l": 0.04,
        "na_mg_l": 0.10,
        "k_mg_l": 0.03,
        "cl_mg_l": 0.18
      },
      "provenance": {
        "ph": "EBAS station override",
        "nh4_mg_l": "CAMS wet deposition / ERA5 precipitation"
      }
    }
  }
}
```

If passing the JSON to existing repository helpers, first confirm the helper's expected unit convention and conversion factors. Do not assume every `*_mg_l` key is currently treated as `1 mg/L = 1 g/m3` by older helper code.
