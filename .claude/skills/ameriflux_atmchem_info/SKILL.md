# Skill: Atmospheric Chemistry & Deposition Extraction (CAMS-EAC4)

## Purpose
Map atmospheric chemical concentrations to the `clmvars_default.json` variables using CAMS Global Reanalysis data and geochemical stoichiometric ratios.

---

## 1. Variable Mapping & CAMS Shortnames
The following table maps the NetCDF template variables to the specific shortnames used in the CAMS Atmosphere Data Store (ADS).

| NetCDF Variable | CAMS Long Name / Parameter | Units (CAMS) |
| :--- | :--- | :--- |
| **CN4RIG** | `wet_deposition_of_ammonium_aerosol` | $kg\ m^{-2}\ s^{-1}$ |
| **CNORIG** | `wet_deposition_of_nitrate_aerosol` | $kg\ m^{-2}\ s^{-1}$ |
| **CSORG** | `wet_deposition_of_sulfate_aerosol` | $kg\ m^{-2}\ s^{-1}$ |
| **CCLRG** | `sea_salt_aerosol_wet_deposition` (Proxy) | $kg\ m^{-2}\ s^{-1}$ |
| **CALRG / CFERG** | `dust_aerosol_wet_deposition` (Calculated) | $kg\ m^{-2}\ s^{-1}$ |
| **Precipitation** | `total_precipitation` (tp) | $m$ (depth) or $kg\ m^{-2}\ s^{-1}$ |

---

## 2. Geochemical Calculations
Since specific ions like Aluminum ($Al$) and Iron ($Fe$) are not standalone in CAMS, they are derived from **Dust Aerosol** deposition using standard crustal abundance ratios:

* **Aluminum (CALRG):** $8\%$ of total Dust Deposition.
* **Iron (CFERG):** $3.5\%$ of total Dust Deposition.
* **Chloride (CCLRG):** Approximated by the sea-salt aerosol fraction.

---

## 3. Concentration Derivation Logic
To convert CAMS flux data into the concentrations required by the model ($g/m^3$):
1.  **Extract Fluxes:** Obtain the wet deposition rate ($D_{wet}$) in $kg\ m^{-2}\ s^{-1}$.
2.  **Extract Precipitation:** Obtain the total precipitation rate ($P$) in $kg\ m^{-2}\ s^{-1}$ (or $mm/s$).
3.  **Apply Formula:** $Concentration\ (g/m^3) = \frac{D_{wet}}{P} \times 1000$.
