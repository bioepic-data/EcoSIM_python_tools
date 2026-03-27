#!/usr/bin/env python3
"""
Convert Ameriflux ERA5 half-hourly climate forcing data to ECOSIM hourly format.

This script processes the ERA5 climate data from the Ameriflux format and converts
it to the ECOSIM climate forcing format.
"""

import pandas as pd
import numpy as np
from netCDF4 import Dataset
import os
from datetime import datetime
import argparse
import math
import warnings
warnings.filterwarnings("ignore")

def parse_timestamps(timestamp_str):
    """Parse timestamp string from Ameriflux data."""
    # Format: YYYYMMDDHHMM (e.g., 198101010000)
    # Convert to string first to ensure it's a string
    timestamp_str = str(timestamp_str)
    year = int(timestamp_str[:4])
    month = int(timestamp_str[4:6])
    day = int(timestamp_str[6:8])
    hour = int(timestamp_str[8:10])
    minute = int(timestamp_str[10:12])
    return datetime(year, month, day, hour, minute)

def calculate_solar_noon_utc(year, month, day, longitude):
    """
    Calculates the time of solar noon in Coordinated Universal Time (UTC).

    Solar noon is the time when the sun is at its highest point in the sky
    (transiting the local celestial meridian).

    This calculation depends on the date (for Equation of Time) and longitude.
    Latitude is not required for the *time* of solar noon, but is included
    in this function's parameters as requested.

    Args:
        year (int): The year (e.g., 2024).
        month (int): The month (1-12).
        day (int): The day (1-31).
        longitude (float): The observer's longitude in degrees.
                       (Positive for East, Negative for West).

    Returns:
        float: The time of solar noon in UTC hours (e.g., 12.5 = 12:30 PM UTC).
    """

    # 1. Calculate the Day of the Year (DOY)
    d = datetime(year, month, day)
    doy = d.timetuple().tm_yday

    # 2. Calculate the Equation of Time (EoT) in minutes
    # This is a common approximation
    # B is in degrees
    B_deg = (360 / 365.24) * (doy - 81)
    # B is in radians
    B_rad = math.radians(B_deg)

    eot = 9.87 * math.sin(2 * B_rad) - 7.53 * math.cos(B_rad) - 1.5 * math.sin(B_rad)

    # 3. Calculate Solar Noon in minutes from UTC midnight
    # 720 = 12:00 (noon) in minutes (12 * 60)
    # 4 * longitude = longitude correction in minutes (Earth rotates 1 degree in 4 mins)
    # We subtract eot from the mean solar noon

    solar_noon_minutes_from_utc_midnight = 720 - (4 * longitude) - eot

    # 4. Convert the minutes into hours
    solar_noon_utc_hours = solar_noon_minutes_from_utc_midnight / 60

    return solar_noon_utc_hours

def convert_era5_to_ecosim(era5_file, output_file, longitude=120.0):
    """
    Convert ERA5 half-hourly data to ECOSIM hourly format.

    Parameters:
    era5_file (str): Path to the Ameriflux ERA5 CSV file
    output_file (str): Path to output netCDF file
    longitude (float): Longitude of the site for solar noon calculation
    """

    # Read the CSV data with dtype specification to avoid automatic conversion
    df = pd.read_csv(era5_file, dtype={'TIMESTAMP_START': str, 'TIMESTAMP_END': str})

    # Parse timestamps
    df['timestamp_start'] = df['TIMESTAMP_START'].apply(parse_timestamps)
    df['timestamp_end'] = df['TIMESTAMP_END'].apply(parse_timestamps)

    # Convert to hourly data by averaging consecutive half-hourly values
    # We need to group by hour and average the values
    df['hour'] = df['timestamp_start'].dt.hour
    df['day_of_year'] = df['timestamp_start'].dt.dayofyear
    df['year'] = df['timestamp_start'].dt.year

    # Create hourly data by grouping consecutive half-hourly data
    hourly_data = []

    # Get unique years
    years = df['year'].unique()

    for year in years:
        year_data = df[df['year'] == year]

        # For each day of the year, we need to process the data
        for day in range(1, 367):  # 1-366 days
            day_data = year_data[year_data['day_of_year'] == day]

            # If we have data for this day, we need to convert to hourly
            if len(day_data) > 0:
                # Process each hour - we need to pair up consecutive half-hourly records
                for hour in range(24):
                    # Get the two half-hourly records for this hour
                    hour_data = day_data[day_data['hour'] == hour]

                    # Check if we have 2 records (one for each half-hour)
                    if len(hour_data) == 2:
                        # Average the two half-hourly values
                        hourly_row = {
                            'year': year,
                            'day': day,
                            'hour': hour,
                            'TMPH': hour_data['TA_ERA'].mean(),  # Air temperature
                            'WINDH': hour_data['WS_ERA'].mean(),  # Wind speed
                            'RAINH': hour_data['P_ERA'].sum(),    # Precipitation (sum over half-hour)
                            'DWPTH': hour_data['VPD_ERA'].mean(), # Vapor pressure (using VPD, need to convert)
                            'SRADH': hour_data['SW_IN_ERA'].mean(), # Solar radiation
                            'PATM': hour_data['PA_ERA'].mean()    # Atmospheric pressure
                        }
                    elif len(hour_data) == 1:
                        # If only one value, use it
                        hourly_row = {
                            'year': year,
                            'day': day,
                            'hour': hour,
                            'TMPH': hour_data['TA_ERA'].iloc[0],
                            'WINDH': hour_data['WS_ERA'].iloc[0],
                            'RAINH': hour_data['P_ERA'].iloc[0],
                            'DWPTH': hour_data['VPD_ERA'].iloc[0],
                            'SRADH': hour_data['SW_IN_ERA'].iloc[0],
                            'PATM': hour_data['PA_ERA'].iloc[0]   # Atmospheric pressure
                        }
                    else:
                        # No data for this hour, fill with missing value
                        hourly_row = {
                            'year': year,
                            'day': day,
                            'hour': hour,
                            'TMPH': 1e30,
                            'WINDH': 1e30,
                            'RAINH': 1e30,
                            'DWPTH': 1e30,
                            'SRADH': 1e30,
                            'PATM': 1e30
                        }
                    hourly_data.append(hourly_row)

    # Create a DataFrame for hourly data
    hourly_df = pd.DataFrame(hourly_data)

    # Create the netCDF file
    create_ecosim_climate_file(hourly_df, output_file, longitude)

def create_ecosim_climate_file(df, output_file, longitude):
    """
    Create ECOSIM climate forcing netCDF file from hourly data.

    Parameters:
    df (DataFrame): Hourly climate data
    output_file (str): Path to output netCDF file
    longitude (float): Longitude of the site for solar noon calculation
    """

    # Create a new netCDF file
    nc_file = Dataset(output_file, 'w', format='NETCDF4')

    # Define dimensions
    nyears = len(df['year'].unique())
    ndays = 366
    nhours = 24
    ngrid = 1

    nc_file.createDimension('year', nyears)
    nc_file.createDimension('day', ndays)
    nc_file.createDimension('hour', nhours)
    nc_file.createDimension('ngrid', ngrid)

    # Create variables
    # Temperature (oC)
    tmp_var = nc_file.createVariable('TMPH', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    tmp_var.long_name = "hourly air temperature"
    tmp_var.units = "oC"

    # Wind speed (m/s)
    wind_var = nc_file.createVariable('WINDH', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    wind_var.long_name = "horizontal wind speed"
    wind_var.units = "m s^-1"

    # Precipitation (mm m^-2 hr^-1) - Need to convert from mm/h to mm m^-2 hr^-1
    rain_var = nc_file.createVariable('RAINH', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    rain_var.long_name = "Total precipitation"
    rain_var.units = "mm m^-2 hr^-1"

    # Vapor pressure (kPa)
    dwpt_var = nc_file.createVariable('DWPTH', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    dwpt_var.long_name = "atmospheric vapor pressure"
    dwpt_var.units = "kPa"

    # Solar radiation (W m^-2)
    srad_var = nc_file.createVariable('SRADH', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    srad_var.long_name = "Incident solar radiation"
    srad_var.units = "W m^-2"

    # Atmospheric pressure (kPa)
    patm_var = nc_file.createVariable('PATM', 'f4', ('year', 'day', 'hour', 'ngrid'), fill_value=1e30)
    patm_var.long_name = "Surface atmospheric pressure"
    patm_var.units = "kPa"

    # Year variable
    year_var = nc_file.createVariable('year', 'i4', ('year',))
    year_var.long_name = "year AD"

    # Other variables with fixed values for this site
    z0g_var = nc_file.createVariable('Z0G', 'f4', ('year', 'ngrid'), fill_value=1e30)
    z0g_var.long_name = "windspeed measurement height"
    z0g_var.units = "m"

    iflgw_var = nc_file.createVariable('IFLGW', 'i4', ('year', 'ngrid'))  # No fill_value for integer variables
    iflgw_var.long_name = "flag for raising Z0G with vegeation"

    znoong_var = nc_file.createVariable('ZNOONG', 'f4', ('year', 'ngrid'), fill_value=1e30)
    znoong_var.long_name = "time of solar noon"
    znoong_var.units = "hour"

    # Create a simple mapping of years to indices
    unique_years = sorted(df['year'].unique())

    # Fill in the data
    for i, year in enumerate(unique_years):
        year_mask = df['year'] == year
        year_data = df[year_mask]

        # Set year value
        year_var[i] = year

        # Fill data for each day and hour
        for day in range(1, 367):
            day_mask = year_data['day'] == day
            if day_mask.any():
                day_data = year_data[day_mask]

                for hour in range(24):
                    hour_mask = day_data['hour'] == hour
                    if hour_mask.any():
                        row = day_data[hour_mask].iloc[0]

                        # Fill variables
                        tmp_var[i, day-1, hour, 0] = row['TMPH']
                        wind_var[i, day-1, hour, 0] = row['WINDH']
                        rain_var[i, day-1, hour, 0] = row['RAINH']
                        dwpt_var[i, day-1, hour, 0] = row['DWPTH']
                        srad_var[i, day-1, hour, 0] = row['SRADH']
                        patm_var[i, day-1, hour, 0] = row['PATM']

    # Set other fixed variables
    for i, year in enumerate(unique_years):
        z0g_var[i, 0] = 1.0  # Fixed value
        iflgw_var[i, 0] = 0  # Fixed value
        # For solar noon calculation, we'll use a fixed date (June 1st) and the site longitude
        znoong_var[i, 0] = calculate_solar_noon_utc(year, 6, 1, longitude)  # Fixed value

    # Close the file
    nc_file.close()

    print(f"ECOSIM climate file created successfully: {output_file}")

def main():
    # Create result directory if it doesn't exist
    result_dir = "result/AMF_US-Ha1"
    os.makedirs(result_dir, exist_ok=True)

    # Input file path
    input_file = "AMF_US-Ha1_FLUXNET_FULLSET_1991-2020_3-5/AMF_US-Ha1_FLUXNET_ERA5_HR_1981-2021_3-5.csv"

    # Output file path
    output_file = os.path.join(result_dir, "ecosim_climate.nc")

    # Site longitude (need to determine from the site data)
    # For Ha1 site, we'll use a typical longitude value for the site
    longitude = -120.0  # Example value - you may need to adjust this

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        return

    print(f"Converting {input_file} to ECOSIM format...")
    convert_era5_to_ecosim(input_file, output_file, longitude=longitude)
    print("Conversion completed successfully!")

if __name__ == "__main__":
    main()