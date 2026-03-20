# Skill: Flux Site to JSON Variable Mapping

## Constraints
- NEVER use it extract climate data.

## Purpose
Automate the identification and derivation of site-specific attributes (e.g., location, vegetation) using Retrieval-Augmented Generation (RAG) to search for information about the specified site and extract required variables.

## 1. Site Metadata Extraction (Flux Network)
Given an American flux site name (e.g., "Blodgett Forest" or "US-Blo"), the skill first will use `pageres` to take an image of the website and then extract the required metadata use the vision RAG tool vision_tool.py. Finally, it will map the extracted metadata to the required JSON variables for the model.

| JSON Variable | Source Attribute | Description |
| :--- | :--- | :--- |
| **ALATG** | Site Latitude | Decimal degrees north. |
| **ALONG** | Site Longitude | Decimal degrees east. |
| **ALTIG** | Elevation | Meters above sea level. |
| **ATCAG** | MAT | Mean Annual Temperature (°C). |
| **IETYPG** | Climate Class | Koppen-Geiger climate zone code. |
| **IXTYP1** | IGBP Type | Dominant vegetation type (mapped to plant litter flags). |

**Logic for Vegetation Mapping:**
* If IGBP is **ENF** (Evergreen Needleleaf) → Set `IXTYP1` to **9** or **11** (Coniferous).
* If IGBP is **DBF** (Deciduous Broadleaf) → Set `IXTYP1` to **8** or **10** (Deciduous).

**Koppen climate classification mapping:**
Using the `koppenDict` mapping, convert the site's Koppen-Geiger code (e.g., "Csa") to the corresponding integer code for `IETYPG`. This will allow the model to apply appropriate climate-specific parameters during simulations.

koppenDict = {
    "Af":  11,
    "Am":  12,
    "As":  13,
    "Aw":  14,
    "BWk": 21,
    "BWh": 22,
    "BSk": 26,
    "BSh": 27,
    "Cfa": 31,
    "Cfb": 32,
    "Cfc": 33,
    "Csa": 34,
    "Csb": 35,
    "Csc": 36,
    "Cwa": 37,
    "Cwb": 38,
    "Cwc": 39,
    "Dfa": 41,
    "Dfb": 42,
    "Dfc": 43,
    "Dfd": 44,
    "Dsa": 45,
    "Dsb": 46,
    "Dsc": 47,
    "Dsd": 48,
    "Dwa": 49,
    "Dwb": 50,
    "Dwc": 51,
    "Dwd": 52,
    "ET": 61,
    "EF": 62
}
## 2. Implementation & Execution

### Prerequisites
* **Python 3.8+**
* **Playwright**: Used to perform the `pageres` equivalent of capturing the site UI.
* **Ollama (Local)**: Must be running with the `qwen2.5vl:7b` model to perform the Vision RAG extraction.

### Setup
```bash
pip install playwright requests
playwright install chromium
ollama pull qwen2.5vl:7b

## Usage
To execute the skill, run the following command from the project root. The resulting JSON will be saved to the `./result/` directory:

```bash
python ./.claude/skills/ameriflux_site_info/extract_ameriflux_site_data.py <SITE_ID>
```

Example:
```bash
python ./.claude/skills/ameriflux_site_info/extract_ameriflux_site_data.py US-Ha1
```

## Output

The script creates a JSON file named `result/<site_name>_ecosim_site.json` with the following structure:

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
