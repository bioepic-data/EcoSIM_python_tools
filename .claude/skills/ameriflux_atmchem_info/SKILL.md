# Skill: tDEP/NADP Atmospheric Chemistry Extractor

## Constraints
- NEVER use it to extract soil data.

## Overview
This tool extracts atmospheric deposition data from the **EPA/NADP Total Deposition (tDEP)** database. It processes high-resolution GeoTIFF files to retrieve chemical concentrations and precipitation totals for a specific geographic location (latitude/longitude) over a user-defined range of years.

The tool automatically handles the **Albers Equal Area Conic** projection used by tDEP and performs unit conversions to provide concentrations in $g/m^3$, matching the requirements for environmental models like EcoSIM.

## Dependencies
The script requires a Python 3.12+ environment with the following libraries:
* **`rasterio`**: For reading and sampling GeoTIFF data.
* **`pyproj`**: For coordinate transformation from WGS84 to the tDEP Albers projection.
* **`argparse`**: For command-line interface management.
* **`json`**: For structured data output.

Install dependencies via pip:
```bash
pip install rasterio pyproj
```

## Data Structure Requirements
The script expects the tDEP database to be organized into year-specific sub-directories within a base folder. Each sub-directory must contain the `.tif` files for the desired chemical species.

**Example tDEP Directory Tree:**
```text
data/tDEP/
├── tDEP-2012/
│   ├── nh4_ww.tif
│   ├── no3_ww.tif
│   └── precip_ww.tif
├── tDEP-2013/
│   ├── ...
```

**Example NADP Directory Tree:**
```text
data/nadp_data_grids/
├── 2012/
│   ├── Ca_conc_2012/conc_ca_2012.tif
│   ├── Cl_conc_2012/conc_cl_2012.tif
│   └── K_conc_2012/conc_k_2012.tif
├── 2013/
│   ├── ...
```

### Variable Mapping
**for tDEP:**
The following variables are extracted and mapped to internal keys:
| Template Variable | tDEP Prefix | Description |
| :--- | :--- | :--- |
| `CN4RIG` | `nh4_ww` | Ammonium ($NH_4$) concentration |
| `CNORIG` | `no3_ww` | Nitrate ($NO_3$) concentration |
| `CSORG` | `s_ww` | Sulfate ($SO_4$) concentration |
| `CCARG` | `ca_ww` | Calcium ($Ca$) concentration |

**for NADP:**
| Template Variable | NADP Prefix | Description |
| :--- | :--- | :--- |
| `PHRG` | `phlab` | pH in precipitation |
| `CN4RIG` | `nh4` | Ammonium ($NH_4$) concentration |
| `CNORIG` | `no3` | Nitrate ($NO_3$) concentration |
| `CSORG` | `so4` | Sulfate ($SO_4$) concentration |
| `CCARG` | `ca` | Calcium ($Ca$) concentration |

NADP extraction must reject NoData, non-finite, negative concentration values, and pH values outside 0-14. The pH raster `phlab` must be emitted under the raw key `ph` so the climate writer can derive `PHRG`.

When the EcoSIM climate forcing writer consumes NADP chemistry, valid annual gaps are filled by linear interpolation with nearest-edge filling. If no valid NADP pH is available for `PHRG`, set `PHRG` to 7 for every year and record that default in the derivation report.

## Usage

### Command Line Arguments
* `--input`: The base path to the tDEP data directory.
* `--output`: Path where the resulting `.json` file will be saved.
* `--longitude`: Longitude in decimal degrees (WGS84).
* `--latitude`: Latitude in decimal degrees (WGS84).
* `--year1`: The starting year of the range (e.g., 2012).
* `--year2`: The ending year of the range (e.g., 2022).

### Execution Example
**To extract atmospheric chemistry data from tDEP for a site located at longitude -72.17 and latitude 42.54 from 2012 to 2022, run the following command:**
```bash
python extract_tdep_range.py \
    --input data/tDEP/ \
    --output results/site_chem.json \
    --longitude -72.17 \
    --latitude 42.54 \
    --year1 2012 \
    --year2 2022
```
***To extract atmospheric chemistry data from NADP for the same site and time range, run:**
```bash
python extract_nadp_range.py \
    --input data/nadp_data_grids/ \
    --output results/site_chem.json \
    --longitude -72.17 \
    --latitude 42.54 \
    --year1 2012 \
    --year2 2022
```

## Technical Details

### Coordinate Transformation
tDEP data is natively stored in a custom Albers Equal Area projection. The script bypasses common `ProjError` issues by manually defining the PROJ string to ensure precise pixel sampling:
`+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs`

### Unit Conversion
**for tDEP:**
The script converts wet deposition flux ($kg/ha$) into atmospheric concentration ($g/m^3$) using the annual precipitation ($P$):
$$Concentration = \frac{Flux_{kg/ha} \times 0.1}{P_{meters}}$$

**for NADP:**
The script converts concentration from $mg/L$ to $g/m^3$ using the formula:
$$Concentration = \frac{Conc_{mg/L}}{1000} \times 1000$$
