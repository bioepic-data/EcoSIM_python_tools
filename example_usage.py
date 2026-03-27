#!/usr/bin/env python3
"""
Example usage script for the ECOSIM NetCDF generator.

This demonstrates how to use the generate_ecosim_netcdf.py script
with a sample configuration.
"""

import os
import sys

def main():
    print("ECOSIM NetCDF Generator - Example Usage")
    print("=" * 40)

    # Check if the script exists
    if not os.path.exists('generate_ecosim_netcdf.py'):
        print("Error: generate_ecosim_netcdf.py not found!")
        sys.exit(1)

    # Show the sample config
    print("\nSample configuration file (sample_config.yaml):")
    print("-" * 40)
    with open('sample_config.yaml', 'r') as f:
        print(f.read())

    print("\nTo run the generator:")
    print("python generate_ecosim_netcdf.py sample_config.yaml")

    print("\nExpected output:")
    print("- Site metadata extracted from AmeriFlux")
    print("- Atmospheric chemistry data extracted from tDEP")
    print("- ECOSIM NetCDF file created at result/ecosim_input.nc")
    print("- File contains all required variables with proper structure")

if __name__ == "__main__":
    main()