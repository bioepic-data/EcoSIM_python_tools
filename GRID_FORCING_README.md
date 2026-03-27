# EcoSIM Grid Forcing Script

## Overview

`create_ecosim_grid_forcing.py` automatically generates EcoSIM grid forcing NetCDF files for AmeriFlux sites by combining two specialized skills:

1. **ameriflux_site_info**: Extracts site metadata (location, elevation, climate, vegetation)
2. **ameriflux_surgo_grid_extract**: Extracts soil profile data from gSSURGO (CONUS database)

The resulting NetCDF file follows the Blodget template structure and contains all necessary grid-level and soil profile information for EcoSIM biogeochemical simulations.

## Requirements

### Python Packages
- `netCDF4`
- `numpy`
- `pandas`
- `pyproj`
- `shapely`
- `pyogrio`
- `playwright`
- `requests`
- `ollama` (local service for vision RAG)

### External Resources
- gSSURGO geodatabase: `data/gSSURGO_CONUS.gdb`
- Blodget template: `templates/Blodget_grid_20251115_modified.nc.template`
- Ollama with `qwen2.5vl:7b` model running locally

### Site Data Requirements
- AmeriFlux site must have a valid site ID (e.g., US-Ha1, US-MMS)
- Site must be located in CONUS (continental United States)
- gSSURGO coverage required for the site location

## Usage

### Basic Usage
```bash
python create_ecosim_grid_forcing.py <SITE_ID>
```

### Example
```bash
python create_ecosim_grid_forcing.py US-Ha1
```

## Output

The script generates the following files in the `result/` directory:

1. **`<SITE_ID>_ecosim_grid.nc`**: Main output NetCDF file
   - Contains all grid-level variables (ALATG, ALTIG, ATCAG, IETYPG, etc.)
   - Contains soil profile data (CDPTH, BKDSI, FC, WP, CSAND, CSILT, PH, CEC, CORGC, etc.)
   - Follows CF conventions with proper units and metadata
   - Dimensions: (ntopou=1, nlevs=20) for soil layers

2. **`<SITE_ID>_ecosim_site.json`**: Site metadata (intermediate)
   - Latitude, longitude, elevation
   - Mean annual temperature
   - Koppen-Geiger climate zone code
   - IGBP vegetation type

3. **`profile_<SITE_ID>.json`**: Soil profile data (intermediate)
   - Raw horizon data from gSSURG O
   - Interpolated values at template depths
   - Source information (MUKEY, COKEY)

## Variables

### Grid-Level Variables (ngrid=1)
- **ALATG**: Site latitude (degrees north)
- **ALTIG**: Elevation (m)
- **ATCAG**: Mean annual temperature (°C)
- **IETYPG**: Koppen climate zone (integer code)
- **IDTBLG**: Water table flag (default: 1 = natural stationary)
- **DHI, DVI**: Grid dimensions

### Topographic Unit Variables (ntopou=1)
- **IXTYP1**: Vegetation type (IGBP code)
- **NJ**: Maximum rooting layer (default: 15)
- **ASPX**: Aspect angle (default: 90°)
- **SL0**: Slope (default: 10°)
- **PH0**: Surface litter pH (default: 5.0)
- Surface litter pools (RSCf, RSNf, RSPf, etc.)

### Soil Profile Variables (with nlevs=20 depth layers)
#### From gSSURGO (where available)
- **CDPTH**: Depth to bottom of soil layer (m)
- **BKDSI**: Bulk density (Mg m⁻³)
- **FC**: Field capacity (m³ m⁻³)
- **WP**: Wilting point (m³ m⁻³)
- **SCNV, SCNH**: Hydraulic conductivity (mm h⁻¹)
- **CSAND**: Sand content (kg Mg⁻¹)
- **CSILT**: Silt content (kg Mg⁻¹)
- **ROCK**: Rock fraction (0-1)
- **PH**: Soil pH
- **CEC**: Cation exchange capacity (cmol kg⁻¹)
- **CORGC**: Soil organic carbon (kg C/Mg soil)

#### From Template Defaults (not in gSSURGO)
- **CORGN**: Soil organic nitrogen (set to -1 = no data)
- **CORGP**: Soil organic phosphorus (set to -1 = no data)
- **CNH4, CNO3, CPO4**: Nutrient pools (template defaults)
- **CA, CFE, CCA, CMG, CNA, CKA, CSO4, CCL**: Cations/anions (template defaults)
- **Phosphate minerals**: CALPO, CFEPO, CCAPD, CCAPH (template defaults)
- **Hydroxides**: CALOH, CFEOH (template defaults)
- **Carbonates**: CCACO, CCASO (template defaults)
- **Gapon coefficients**: GKC4, GKCH, GKCA, GKCM, GKCN, GKCK (template defaults)

## Data Processing Workflow

### Step 1: Site Information Extraction
- Uses vision RAG (Qwen2.5-VL) to extract site metadata from AmeriFlux website
- Creates `<SITE_ID>_ecosim_site.json` with:
  - Latitude, longitude, elevation
  - Mean annual temperature
  - Koppen climate classification

### Step 2: Soil Profile Extraction
- Queries gSSURGO geodatabase using site coordinates
- Performs spatial lookup to find grid cell (MUKEY)
- Selects dominant soil component (by COMPPCT_R)
- Extracts all soil horizons from CHORIZON table
- Vertically interpolates to template depth structure
- Applies log-interpolation for organic matter (CORGC)
- Exports to `profile_<SITE_ID>.json`

### Step 3: NetCDF Creation
- Creates NetCDF4 file with proper dimensions
- Populates grid-level variables from site_info
- Populates soil variables from gSSURGO data (with defaults as fallback)
- Uses -999.9 as fill value for missing data
- Adds CF conventions metadata (units, long_name, etc.)

## Handling Missing Data

### Incomplete gSSURGO Data
If certain soil variables are not available from gSSURGO:
- Use template default values as fallback
- Mark with `-999.9` fill value where appropriate
- Document in processing log

### Incomplete Site Information
If vision RAG fails to extract site metadata:
- Check Ollama service is running: `ollama serve`
- Verify Qwen model is installed: `ollama pull qwen2.5vl:7b`
- Manually enter values in intermediate JSON files

### gSSURGO Database Issues
If spatial query returns no data:
- Verify site coordinates are in CONUS
- Check gSSURGO geodatabase path is correct
- Ensure geodatabase contains required tables (MUPOLYGON, COMPONENT, CHORIZON)

## Template Structure

The Blodget template (`templates/Blodget_grid_20251115_modified.nc.template`) defines:
- Dimension sizes: ngrid=1, ntopou=1, nlevs=20, nrow=1, ncol=1
- Variable names and attributes from EcoSIM model requirements
- Default values for parameters not obtainable from data sources
- Depth structure for soil layers (down to 10 m)

## Processing Notes

1. **Vertical Interpolation**: 
   - Most variables use overlap-weighted averaging across depth layers
   - Organic carbon (CORGC) uses log-space interpolation to preserve exponential trends

2. **Data Units**:
   - All depths in meters
   - Bulk density in Mg m⁻³ (megagrams per cubic meter)
   - Hydraulic conductivity converted from µm/s to mm/h
   - Texture content in kg Mg⁻¹
   - pH unitless; CEC in cmol/kg

3. **Layer Extension**:
   - With `--extend-last`, deepest horizon is extended downward to cover deeper template layers
   - Prevents gaps in deep soil profiles

4. **Fill Values**:
   - Set to -999.9 for missing data
   - NetCDF file includes FillValue attribute for each variable
   - Users should treat these as "no data"

## Example: Creating Grid Files for Multiple Sites

```bash
for site in US-Ha1 US-Ha3 US-MMS; do
  python create_ecosim_grid_forcing.py $site
done
```

## References

- AmeriFlux: https://ameriflux.lbl.gov/
- gSSURGO: https://sdmdataaccess.sc.egov.usda.gov/
- Blodget Forest site: https://ameriflux.lbl.gov/sites/siteinfo/US-Ha1
- EcoSIM Model: https://agsci.oregonstate.edu/npp/research/ecosim

## Troubleshooting

### Script hangs after "Extracting site information..."
- Ollama service may not be running
- Run `ollama serve` in another terminal
- Check network connectivity for website access

### "No MUPOLYGON features found"
- Site coordinates outside CONUS
- gSSURGO database doesn't have coverage for that location
- Verify coordinates are correct

### NetCDF file created but incomplete
- Check `result/profile_<SITE_ID>.json` for soil data
- If missing, SURGO extraction failed; check error log
- Use template defaults for missing variables

### Memory issues with large gSSURGO database
- The pyogrio library reads entire GDB into memory
- Optimize by querying smaller geographic extents
- Consider extracting profiles in batches

## Contact & Support

For questions about:
- **Site information extraction**: See `.claude/skills/ameriflux_site_info/SKILL.md`
- **SURGO data extraction**: See `.claude/skills/ameriflux_surgo_grid_extract/SKILL.md`
- **NetCDF structure**: See template file documentation in `templates/`
