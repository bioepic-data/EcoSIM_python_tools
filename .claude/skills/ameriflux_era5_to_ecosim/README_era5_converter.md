# ERA5 to ECOSIM Climate Converter

This tool converts Ameriflux ERA5 half-hourly climate forcing data into the ECOSIM hourly climate format.

## Overview

The converter reads half-hourly climate data from Ameriflux ERA5 format and transforms it into the ECOSIM climate forcing format as specified in the `Blodget.clim.2012-2022.template` file.

## Input Format

The input is a CSV file with the following columns:
- `TIMESTAMP_START`: Start timestamp (YYYYMMDDHHMM)
- `TIMESTAMP_END`: End timestamp (YYYYMMDDHHMM)
- `TA_ERA`: Air temperature (°C)
- `SW_IN_ERA`: Shortwave incoming radiation (W m⁻²)
- `LW_IN_ERA`: Longwave incoming radiation (W m⁻²)
- `VPD_ERA`: Vapor pressure deficit (kPa)
- `PA_ERA`: Atmospheric pressure (hPa)
- `P_ERA`: Precipitation (mm h⁻¹)
- `WS_ERA`: Wind speed (m s⁻¹)

## Output Format

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

## Usage

```bash
python era5_to_ecosim_converter.py --input AMF_US-Ha1_FLUXNET_ERA5_HR_1981-2021_3-5.csv --output ecosim_climate.nc
```

## Conversion Process

1. Reads half-hourly data from the input CSV
2. Averages consecutive half-hourly values to create hourly data
3. Maps ERA5 variables to ECOSIM variable names and units
4. Creates a netCDF file in the ECOSIM format
5. Handles missing data with appropriate fill values

## Notes

- The converter handles missing data by using fill values (1e30)
- Precipitation is summed over the half-hour period to get hourly values
- Temperature, wind speed, and solar radiation are averaged over the half-hour period
- Vapor pressure deficit is used directly as atmospheric vapor pressure