# Skill: Convert Ameriflux ERA5 Climate Data to ECOSIM Format

## Constraints
- NEVER use it extract soil data.

## Overview

This skill converts Ameriflux ERA5 half-hourly climate forcing data into the ECOSIM hourly climate format. The conversion process transforms climate data from the ERA5 format (provided by Ameriflux) to the ECOSIM climate forcing format as specified in the `Blodget.clim.2012-2022.template` file.

## Input Data Format

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

## Conversion Process

1. **Data Reading**: Reads half-hourly climate data from the input CSV file
2. **Timestamp Parsing**: Converts timestamp strings to datetime objects
3. **Data Aggregation**: Averages consecutive half-hourly values to create hourly data
4. **Variable Mapping**: Maps ERA5 variables to ECOSIM variable names and units
5. **NetCDF Creation**: Creates a properly formatted netCDF file in ECOSIM format

## Usage
To execute the skill, run the following command from the project root. The resulting JSON will be saved to the `./result/` directory:

```bash
python ./.claude/skills/ameriflux_era5_to_ecosim/era5_to_ecosim_converter.py --input data/data/AMF_US-Ha1_FLUXNET_FULLSET_1991-2020_3-5/AMF_US-Ha1_FLUXNET_ERA5_HR_1981-2021_3-5.csv --output result/ecosim_climate.nc --site-id US-Ha1
```

## Key Features

- Handles missing data with appropriate fill values (1e30 for float variables)
- Properly converts precipitation from half-hourly to hourly values (summing)
- Averages temperature, wind speed, and solar radiation over half-hour periods
- Supports multiple years of data
- Creates valid netCDF files with proper metadata

## Limitations

- Assumes that each hour has exactly two half-hourly records
- For hours with missing data, uses fill values (1e30)
- Does not handle complex climate data processing beyond simple averaging

## Requirements

- Python 3.6+
- pandas
- numpy
- netCDF4