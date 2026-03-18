# AmeriFlux Site Data Extractor (RAG-based)

This script extracts site-specific data from AmeriFlux webpages using a Retrieval-Augmented Generation (RAG) approach and converts it to the EcoSIM format as required by the `ameriflux_site_info` skill.

## Purpose

The script automates the extraction of key site attributes (coordinates, vegetation, climate) from AmeriFlux site webpages using RAG techniques and formats them according to EcoSIM's requirements.

## Required Dependencies

```bash
pip install requests beautifulsoup4
```

## Usage

```bash
python extract_ameriflux_site_data.py <site_name>
```

Example:
```bash
python extract_ameriflux_site_data.py US-Ha1
```

## Output

The script creates a JSON file named `<site_name>_ecosim_site.json` with the following structure:

```json
{
  "site_name": "US-Ha1",
  "ALATG": 40.0,      # Latitude (decimal degrees north)
  "ALONG": -120.0,    # Longitude (decimal degrees east)
  "ALTIG": 1000.0,    # Elevation (meters above sea level)
  "ATCAG": 10.0,      # Mean Annual Temperature (°C)
  "IETYPG": 34,       # Koppen climate zone code
  "IXTYP1": 10        # Vegetation type code
}
```

## How It Works

1. The script uses a RAG approach to search for site information by trying multiple URL patterns
2. It parses the HTML content to extract key site attributes:
   - Latitude, longitude, elevation
   - Mean Annual Temperature (MAT)
   - Koppen climate classification
   - IGBP vegetation type
3. It maps IGBP vegetation types to EcoSIM's IXTYP1 codes
4. It converts Koppen climate codes to integer codes used by EcoSIM
5. If real data cannot be fetched, it creates a sample fallback file with reasonable default values

## RAG Approach

The RAG-based approach works by:
- First attempting direct URL access to AmeriFlux site pages
- If that fails, performing a web search to find the site page
- Using BeautifulSoup to parse HTML and extract required information
- Applying pattern matching to identify coordinates, climate codes, and vegetation types

## Site Data Mapping

### Koppen Climate Codes (IETYPG)
- Af: 11, Am: 12, As: 13, Aw: 14
- BWk: 21, BWh: 22, BSk: 26, BSh: 27
- Cfa: 31, Cfb: 32, Cfc: 33, Csa: 34, Csb: 35, Csc: 36
- Cwa: 37, Cwb: 38, Cwc: 39
- Dfa: 41, Dfb: 42, Dfc: 43, Dfd: 44, Dsa: 45, Dsb: 46, Dsc: 47, Dsd: 48
- Dwa: 49, Dwb: 50, Dwc: 51, Dwd: 52
- ET: 61, EF: 62

### IGBP to EcoSIM Vegetation Mapping (IXTYP1)
- ENF (Evergreen Needleleaf): 11 (Coniferous)
- DBF (Deciduous Broadleaf): 10 (Deciduous)
- Other IGBP types: 10 (Deciduous, default)

## Fallback Behavior

When real data cannot be fetched from the AmeriFlux website, the script creates a sample JSON file with:
- Sample coordinates (40.0°N, -120.0°E)
- Sample elevation (1000.0m)
- Sample temperature (10.0°C)
- Sample Koppen climate code (Csa = 34)
- Sample vegetation type (Deciduous = 10)

This ensures the script always produces valid output for testing and development purposes.