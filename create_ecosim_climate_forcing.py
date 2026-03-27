#!/usr/bin/env python3
"""
Create EcoSIM climate forcing NetCDF for an AmeriFlux site.

This script combines multiple skills to generate a complete EcoSIM climate forcing file:
1. Extract site information (lat/lon, etc.) from AmeriFlux
2. Convert ERA5 climate data to EcoSIM format
3. Extract atmospheric chemistry data
4. Combine everything into a single NetCDF file
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
import pandas as pd
from netCDF4 import Dataset
import numpy as np

def run_site_info(site_id, output_dir="result"):
    """Run the site info extraction."""
    script_path = ".claude/skills/ameriflux_site_info/extract_ameriflux_site_data.py"
    cmd = [sys.executable, script_path, site_id]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        print(f"Error running site info: {result.stderr}")
        return None
    
    site_file = f"{output_dir}/{site_id}_ecosim_site.json"
    if os.path.exists(site_file):
        with open(site_file, 'r') as f:
            return json.load(f)
    return None

def find_era5_file(site_id, data_dir="data"):
    """Find the ERA5 CSV file for the site."""
    # Look for directories starting with AMF_<site_id>
    for item in os.listdir(data_dir):
        if item.startswith(f"AMF_{site_id}_") and os.path.isdir(os.path.join(data_dir, item)):
            # Look for ERA5_HR file
            for file in os.listdir(os.path.join(data_dir, item)):
                if "ERA5_HR" in file and file.endswith(".csv"):
                    return os.path.join(data_dir, item, file)
    return None

def run_era5_conversion(era5_file, output_file, site_id):
    """Run the ERA5 to EcoSIM conversion."""
    script_path = ".claude/skills/ameriflux_era5_to_ecosim/era5_to_ecosim_converter.py"
    cmd = [sys.executable, script_path, "--input", era5_file, "--output", output_file, "--site-id", site_id]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        print(f"Error running ERA5 conversion: {result.stderr}")
        return False
    return True

def extract_chemistry(lat, lon, years, output_file, chem_dir="data/nadp_data_grids"):
    """Extract atmospheric chemistry data."""
    # Check if chemistry data directory exists
    if not os.path.exists(chem_dir):
        print(f"  Error: NADP data directory not found: {chem_dir}")
        return None
    
    script_path = ".claude/skills/ameriflux_atmchem_info/extract_nadp_range.py"
    start_year = min(years)
    end_year = max(years)
    cmd = [sys.executable, script_path, 
           "--input", chem_dir,
           "--output", output_file,
           "--longitude", str(lon),
           "--latitude", str(lat),
           "--year1", str(start_year),
           "--year2", str(end_year)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        print(f"  Error running chemistry extraction: {result.stderr}")
        return None
    
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            chem_data = json.load(f)
            # Validate that data was actually extracted
            if 'data_by_year' in chem_data and len(chem_data['data_by_year']) > 0:
                # Count how many years have data
                years_with_data = sum(1 for year_data in chem_data['data_by_year'].values() 
                                     if year_data.get('raw_ion_conc', {}) or year_data.get('elemental_conc', {}))
                if years_with_data > 0:
                    print(f"  Chemistry: Successfully extracted data for {years_with_data} out of {len(chem_data['data_by_year'])} years")
                    return chem_data
                else:
                    print(f"  Chemistry: No meaningful ion concentration data found for any year")
                    return None
            else:
                print(f"  Chemistry: No year data in extraction results")
                return None
    return None

def add_chemistry_to_netcdf(netcdf_file, chemistry_data, years):
    """Add chemistry variables to the NetCDF file with gap filling."""
    # Mapping from chemistry data to NetCDF variables
    chem_mapping = {
        'nh4_mg_l': ('CN4RIG', 0.7765, 'gN m^-3', 'NH4 conc in precip'),
        'no3_mg_l': ('CNORIG', 0.2259, 'gN m^-3', 'NO3 conc in precip'),
        'so4_mg_l': ('CSORG', 0.3338, 'gS m^-3', 'SO4 conc in precip'),
        'ca_mg_l': ('CCARG', 1.0, 'gCa m^-3', 'Ca conc in precip'),
        'mg_mg_l': ('CMGRG', 1.0, 'gMg m^-3', 'Mg conc in precip'),
        'na_mg_l': ('CNARG', 1.0, 'gNa m^-3', 'Na conc in precip'),
        'k_mg_l': ('CKARG', 1.0, 'gK m^-3', 'K conc in precip'),
        'cl_mg_l': ('CCLRG', 1.0, 'gCl m^-3', 'Cl conc in precip'),
        'ph': ('PHRG', 1.0, 'pH', 'pH in precipitation')
    }
    
    with Dataset(netcdf_file, 'a') as nc:
        # Get years from the file
        file_years = nc.variables['year'][:]
        
        for var_name, (nc_var, factor, units, long_name) in chem_mapping.items():
            if nc_var not in nc.variables:
                # Create the variable
                var = nc.createVariable(nc_var, 'f4', ('year', 'ngrid'), fill_value=1e30)
                var.long_name = long_name
                var.units = units
            
            # Collect available data for this variable
            available_data = {}
            for i, year in enumerate(file_years):
                year_str = str(int(year))
                if year_str in chemistry_data.get('data_by_year', {}):
                    year_data = chemistry_data['data_by_year'][year_str]
                    raw_data = year_data.get('raw_ion_conc', {})
                    if var_name in raw_data:
                        value = raw_data[var_name] * factor / 1000  # mg/L to g/L = g/m3
                        available_data[i] = value
            
            # Fill gaps using the specified strategy
            if available_data:
                # Get sorted indices of available data
                available_indices = sorted(available_data.keys())
                first_available_idx = available_indices[0]
                last_available_idx = available_indices[-1]
                
                # Fill each year
                for i in range(len(file_years)):
                    if i in available_data:
                        # Use available data
                        nc.variables[nc_var][i, 0] = available_data[i]
                    else:
                        # Fill gaps
                        if i < first_available_idx:
                            # Beginning gap: use first available value
                            nc.variables[nc_var][i, 0] = available_data[first_available_idx]
                        elif i > last_available_idx:
                            # End gap: use last available value
                            nc.variables[nc_var][i, 0] = available_data[last_available_idx]
                        else:
                            # Middle gap: nearest neighbor interpolation
                            # Find the closest available indices
                            prev_idx = max(idx for idx in available_indices if idx < i)
                            next_idx = min(idx for idx in available_indices if idx > i)
                            
                            # Use nearest neighbor (simpler than interpolation for this use case)
                            if abs(i - prev_idx) <= abs(i - next_idx):
                                nc.variables[nc_var][i, 0] = available_data[prev_idx]
                            else:
                                nc.variables[nc_var][i, 0] = available_data[next_idx]

def get_years_from_era5(era5_file):
    """Extract years from ERA5 CSV file."""
    df = pd.read_csv(era5_file, dtype={'TIMESTAMP_START': str})
    df['year'] = df['TIMESTAMP_START'].str[:4].astype(int)
    return sorted(df['year'].unique())

def main():
    parser = argparse.ArgumentParser(description='Create EcoSIM climate forcing NetCDF for AmeriFlux site')
    parser.add_argument('site_id', help='AmeriFlux site ID (e.g., US-Ha1)')
    parser.add_argument('--output', '-o', help='Output NetCDF file path')
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--result-dir', default='result', help='Result directory')
    
    args = parser.parse_args()
    
    site_id = args.site_id
    data_dir = args.data_dir
    result_dir = args.result_dir
    
    # Ensure result directory exists
    os.makedirs(result_dir, exist_ok=True)
    
    # Default output file
    if not args.output:
        args.output = f"{result_dir}/{site_id}_ecosim_climate.nc"
    
    print(f"Processing site: {site_id}")
    
    # Step 1: Get site information
    print("Step 1: Extracting site information...")
    site_data = run_site_info(site_id, result_dir)
    if not site_data:
        print("Failed to extract site information")
        return
    
    lat = site_data['ALATG']
    lon = site_data['ALONG']
    print(f"Site location: {lat}, {lon}")
    
    # Step 2: Find ERA5 file
    print("Step 2: Finding ERA5 data file...")
    era5_file = find_era5_file(site_id, data_dir)
    if not era5_file:
        print(f"ERA5 file not found for site {site_id}")
        return
    
    print(f"Found ERA5 file: {era5_file}")
    
    # Get years from ERA5 file
    years = get_years_from_era5(era5_file)
    print(f"Years in data: {years}")
    
    # Step 3: Convert ERA5 to NetCDF
    print("Step 3: Converting ERA5 data to EcoSIM format...")
    temp_nc = args.output + '.temp'
    if not run_era5_conversion(era5_file, temp_nc, site_id):
        print("Failed to convert ERA5 data")
        return
    
    # Step 4: Extract chemistry data
    print("Step 4: Extracting atmospheric chemistry...")
    chem_file = f"{result_dir}/{site_id}_chemistry.json"
    chem_dir = f"{data_dir}/nadp_data_grids"
    
    # Check if chemistry directory exists and has content
    if not os.path.exists(chem_dir):
        print(f"  Warning: Chemistry data directory not found: {chem_dir}")
        print("  Continuing without atmospheric chemistry data...")
        chemistry_data = None
    else:
        chemistry_data = extract_chemistry(lat, lon, years, chem_file, chem_dir)
        if not chemistry_data:
            print("  Chemistry extraction did not return usable data")
            print("  Continuing without atmospheric chemistry data...")
        else:
            print("  Chemistry data will be added to NetCDF")
    
    # Step 5: Add chemistry to NetCDF
    print("Step 5: Adding chemistry to NetCDF...")
    if chemistry_data:
        add_chemistry_to_netcdf(temp_nc, chemistry_data, years)
    else:
        print("No chemistry data available, skipping chemistry addition")
    
    # Rename temp file to final output
    os.rename(temp_nc, args.output)
    
    print(f"Successfully created EcoSIM climate file: {args.output}")

if __name__ == "__main__":
    main()