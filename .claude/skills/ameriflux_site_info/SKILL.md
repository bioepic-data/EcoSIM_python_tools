# Skill: Flux Site to JSON Variable Mapping

## Purpose
Automate the identification and derivation of site-specific attributes (e.g., location, vegetation) using Retrieval-Augmented Generation (RAG) to search for information about the specified site and extract required variables.

## 1. Site Metadata Extraction (Flux Network)
Given an American flux site name (e.g., "Blodgett Forest" or "US-Blo"), extract core coordinates and vegetation characteristics using RAG-based search.

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