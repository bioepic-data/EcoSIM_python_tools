# Skill: Automated AmeriFlux Soil Profiling (GeoPackage)

This skill automates the generation of 20-layer soil profiles for multiple AmeriFlux sites using a local SSURGO GeoPackage and the specific variable mappings for the NetCDF template.

## 1. Automation Workflow
1. **Site Batching:** Input a list of AmeriFlux Site IDs with their associated Latitude and Longitude.
2. **Spatial Intersection:** Perform a point-in-polygon lookup against the `mupolygon` layer to retrieve the `mukey`.
3. **Data Retrieval:** Query `component` and `chorizon` tables locally within the GeoPackage.

## 2. Variable Derivation Logic
| NetCDF Variable | gSSURGO Attribute | Formula / Logic |
| :--- | :--- | :--- |
| **BKDSI** | `dbthirdbar_r` | Initial bulk density ($Mg/m^3$) [cite: 53] |
| **SCNV** | `ksat_r` | $\mu m/s 	imes 3.6 	o mm/h$ [cite: 57] |
| **CSAND** | `sandtotal_r` | $\% 	imes 10 	o kg/Mg$ [cite: 59] |
| **ROCK** | `fragvol_r` | $\% / 100 	o$ fraction (0.0-1.0) [cite: 62] |
| **CORGC** | `om_r` | $(OM\% / 1.724) 	imes 10 	o kg C/Mg$ [cite: 67] |

## 3. Step C: Vertical Scaling (20 Layers)
* **Objective:** Ensure every site has exactly 20 layers (`nlevs`).
* **Mapping:** If a model layer depth falls within a gSSURGO horizon, use that horizon's data.
* **Extrapolation:** If the model depth exceeds the total depth of the soil survey (e.g., model depth is 2.5m but survey stops at 2.0m), the properties of the bottom-most horizon must be duplicated for all deeper layers .
* **Missing Data:** Assign the FillValue `-999.9` to any missing numeric attributes[cite: 52, 64].

## 4. Troubleshooting
* **Memory Management:** Use a spatial mask when reading `mupolygon` to avoid loading the entire 10GB+ file into memory.
* **Coordinate Systems:** Always confirm AmeriFlux coordinates are in WGS84 (EPSG:4326) before intersecting with the GeoPackage.

