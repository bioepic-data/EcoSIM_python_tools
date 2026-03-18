#!/usr/bin/env python3
"""
Test script for the ERA5 to ECOSIM converter.
"""

import pandas as pd
import numpy as np
from era5_to_ecosim_converter import convert_era5_to_ecosim
import os

def test_converter():
    """Test the converter with a small sample of data."""

    # Create a small test CSV file with just a few rows to avoid complexity
    test_data = """TIMESTAMP_START,TIMESTAMP_END,TA_ERA,SW_IN_ERA,LW_IN_ERA,VPD_ERA,PA_ERA,P_ERA,WS_ERA
198101010000,198101010100,-15.47,0.0,197.941,0.479,98.502,0.0,1.513
198101010100,198101010200,-15.342,0.0,180.489,0.466,98.541,0.0,1.468
198101010200,198101010300,-15.952,0.0,178.778,0.43,98.56,0.0,1.361
198101010300,198101010400,-16.266,0.0,177.859,0.42,98.555,0.0,1.519"""

    # Write test data to a temporary file
    with open('test_era5_data.csv', 'w') as f:
        f.write(test_data)

    try:
        # Test the converter
        convert_era5_to_ecosim('test_era5_data.csv', 'test_ecosim_output.nc')
        print("Test completed successfully!")
        print("Output file 'test_ecosim_output.nc' created.")

        # Check if file was created
        if os.path.exists('test_ecosim_output.nc'):
            print("Output file exists as expected.")
        else:
            print("ERROR: Output file was not created.")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test files
        try:
            os.remove('test_era5_data.csv')
            os.remove('test_ecosim_output.nc')
        except:
            pass

if __name__ == "__main__":
    test_converter()