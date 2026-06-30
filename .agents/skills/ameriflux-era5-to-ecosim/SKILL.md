---
name: ameriflux-era5-to-ecosim
description: Convert AmeriFlux ERA5 half-hourly meteorological CSV files into EcoSIM hourly climate forcing NetCDF files. Use when preparing EcoSIM climate inputs from AmeriFlux ERA5 variables and when validating physical ranges or writing quality reports. For non-AmeriFlux paper sites that need a fresh Copernicus CDS ERA5 point download by longitude/latitude, use era5-cds-point-download first.
---

# AmeriFlux ERA5 to EcoSIM Converter

## Use When

- You need to convert AmeriFlux ERA5 CSV forcing data to EcoSIM NetCDF climate forcing.
- You need hourly `TMPH`, `WINDH`, `RAINH`, `DWPTH`, `SRADH`, or `PATM` variables.
- You need range-aware quality control and a JSON quality report for climate forcing.
- You already have an AmeriFlux-format ERA5 CSV. If the task is to download global CDS ERA5 point data for a non-AmeriFlux literature site, use `era5-cds-point-download` before any EcoSIM conversion.

## Constraints
- NEVER use it extract soil data.

## Overview

This skill converts Ameriflux ERA5 half-hourly climate forcing data into the ECOSIM hourly climate format. The conversion process transforms climate data from the ERA5 format (provided by Ameriflux) to the ECOSIM climate forcing format as specified in the `Blodget.clim.2012-2022.template` file.

For ordinary paper-derived sites outside AmeriFlux/FLUXNET, keep ERA5 acquisition separate: use `era5-cds-point-download` to retrieve Copernicus CDS point time series by longitude/latitude, inspect source units and accumulation conventions, then adapt or convert the data into the AmeriFlux-format columns expected here only after those units are verified.

## Input Data Format

The input is a CSV file with the following columns:
- `TIMESTAMP_START`: Start timestamp (YYYYMMDDHHMM)
- `TIMESTAMP_END`: End timestamp (YYYYMMDDHHMM)
- `TA_ERA`: Air temperature (°C)
- `SW_IN_ERA`: Shortwave incoming radiation (W m⁻²)
- `LW_IN_ERA`: Longwave incoming radiation (W m⁻²)
- `VPD_ERA`: Vapor pressure deficit (hPa in AmeriFlux ERA5 products)
- `PA_ERA`: Atmospheric pressure (kPa)
- `P_ERA`: Precipitation (mm h⁻¹)
- `WS_ERA`: Wind speed (m s⁻¹)

Pay close attention to the source ERA5 time step before conversion. AmeriFlux
archives may provide `ERA5_HH` half-hourly files or `ERA5_HR` hourly files, and
precipitation aggregation must match that cadence to avoid doubling or otherwise
distorting the water input.

## Output Data Format

The output is a netCDF file with the following variables:
- `TMPH`: Hourly air temperature (°C)
- `WINDH`: Hourly wind speed (m s⁻¹)
- `RAINH`: Hourly precipitation (mm m⁻² hr⁻¹)
- `DWPTH`: Hourly atmospheric vapor pressure (kPa)
- `SRADH`: Hourly incident solar radiation (W m⁻²)
- `PATM`: Hourly Surface atmospheric pressure (kPa)
- `year`: Year AD
- `Z0G`: Windspeed measurement height (m)
- `IFLGW`: Flag for raising Z0G with vegetation
- `ZNOONG`: Time of solar noon (hour)

## Workflow

1. **Data Reading**: Reads half-hourly climate data from the input CSV file
2. **Timestamp Parsing**: Converts timestamp strings to datetime objects
3. **Data Aggregation**: Averages consecutive half-hourly values to create hourly data
4. **Quality Control**: Masks physically invalid values before aggregation and fills those gaps by time interpolation.
5. **Variable Mapping**: Maps ERA5 variables to ECOSIM variable names and units
6. **NetCDF Creation**: Creates a properly formatted netCDF file in ECOSIM format

## Physical Range Checks

The converter must ensure derived climate values are in legitimate ranges before writing EcoSIM NetCDF:
- `TMPH` from `TA_ERA`: -90 to 60 degC.
- `WINDH` from `WS_ERA`: 0 to 75 m s^-1.
- `RAINH` from `P_ERA`: non-negative source precipitation.
- `DWPTH` from `VPD_ERA`: non-negative source vapor pressure deficit.
- `SRADH` from `SW_IN_ERA`: 0 to 1400 W m^-2.
- `PATM` from `PA_ERA`: kPa bounds centered on site elevation when `ALTIG` is available, otherwise broad physical fallback bounds.

For sentinel values, non-finite values, and values outside these bounds, mask the value and interpolate along the half-hourly time axis. Use nearest-edge filling only at the beginning or end of the available source period. Emit a JSON quality report when `--quality-report` is supplied.

## Usage
To execute the skill, run the following command from the project root. The resulting JSON will be saved to the `./result/` directory:

```bash
python .agents/skills/ameriflux-era5-to-ecosim/era5_to_ecosim_converter.py --input data/AMF_US-Ha1_FLUXNET_FULLSET_1991-2020_3-5/AMF_US-Ha1_FLUXNET_ERA5_HR_1981-2021_3-5.csv --output result/ecosim_climate.nc --site-id US-Ha1 --quality-report result/US-Ha1/US-Ha1_era5_quality_report.json
```

## Key Features

- Handles physically invalid source data by interpolation before NetCDF writing
- Properly converts precipitation from half-hourly to hourly values (summing)
- Averages temperature, wind speed, and solar radiation over half-hour periods
- Supports multiple years of data
- Creates valid netCDF files with proper metadata

## Limitations

- Calendar padding that is not present in the source data may still use EcoSIM fill values.
- Does not handle complex climate data processing beyond simple averaging

## Requirements

- Python 3.6+
- pandas
- numpy
- netCDF4
