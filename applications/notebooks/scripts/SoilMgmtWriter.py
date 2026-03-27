import json
import numpy as np
from netCDF4 import Dataset, stringtochar

def create_netcdf_from_cdl_schema(json_file_path, nc_file_path):
    # Load the processed JSON data [cite: 1]
    with open(json_file_path, 'r') as f:
        full_json = json.load(f)
        data = full_json.get("processed_soil_management", {})

    # Extract dynamic parameters from JSON [cite: 18]
    year_list = data.get("year", [])
    if not year_list:
        raise ValueError("No year data found in the input JSON.")
    num_years = len(year_list)

    # 1. Create the NetCDF file [cite: 1]
    rootgrp = Dataset(nc_file_path, "w", format="NETCDF3_64BIT_OFFSET")

    # 2. Define Dimensions based on CDL [cite: 1, 2]
    rootgrp.createDimension("ntopou", 1)
    rootgrp.createDimension("year", num_years)
    rootgrp.createDimension("string10", 10)
    rootgrp.createDimension("nfert", 12)
    rootgrp.createDimension("string128", 128)
    rootgrp.createDimension("ntill", 12)
    rootgrp.createDimension("string24", 24)

    # 3. Global Attributes [cite: 16]
    rootgrp.description = "soil managment data created on 2025-12-17 14:10:30\n"

    # 4. Define and Fill Variables [cite: 17]
    # Integer Variables
    int_vars = {
        "NH1": "starting column from the west for a topo unit",
        "NV1": "ending column at the east for a topo unit",
        "NH2": "starting row from the north for a topo unit",
        "NV2": "ending row at the south for a topo unit"
    }
    for var_name, long_name in int_vars.items():
        v = rootgrp.createVariable(var_name, "i4", ("ntopou",))
        v.units = "None"
        v.long_name = long_name
        v[:] = np.array(data.get(var_name, [0]))

    # Year Variable [cite: 18]
    years_var = rootgrp.createVariable("year", "i4", ("year",))
    years_var.long_name = "year AD"
    years_var[:] = np.array(year_list)

    # Topo-unit info strings (fertf, tillf, irrigf) [cite: 7, 8, 9]
    char_vars = {
        "fertf": ("Fertilization info for a topo unit", "string10"),
        "tillf": ("Tillage info for a topo unit", "string10"),
        "irrigf": ("Irrigation info for a topo unit", "string10")
    }
    for v_name, (long_name, dim_name) in char_vars.items():
        v = rootgrp.createVariable(v_name, "S1", ("year", "ntopou", dim_name))
        v.units = "None"
        v.long_name = long_name
        
        # Extract strings and format to 10 chars [cite: 19, 20, 22]
        flat_list = [item[0] if isinstance(item, list) else str(item) for item in data.get(v_name, [])]
        
        # Reshape to (11, 1) and convert to 3D char array (11, 1, 10)
        temp_strings = np.array(flat_list, dtype='S10').reshape(num_years, 1)
        v[:] = stringtochar(temp_strings)


    # Annual Fertilization Variables [cite: 11-16]
    VAR_KEYS = [
        "DDMMYYYY", "NH4Soil", "NH3Soil", "UreaSoil", "NO3Soil", "NH4Band", "NH3Band", 
        "UreaBand", "NO3Band", "MonocalciumPhosphateSoil", "MonocalciumPhosphateBand", 
        "hydroxyapatite", "LimeStone", "Gypsum", "PlantResC", "PlantResN", "PlantResP", 
        "ManureC", "ManureN", "ManureP", "AppDepth", "BandWidth", "PO4Soil", "PO4Band", 
        "IsAmendtypFert", "IsAmendtypResidual", "IsAmendtypManure"
    ]

    for y in year_list:
        var_name = f"fertf_{y}"
        if var_name in data:
            v = rootgrp.createVariable(var_name, "S1", ("nfert", "string128"))
            v.long_name = "fertilization file"
            
            str_list = []
            entries = data[var_name]
            for i in range(12): # Matches nfert dimension [cite: 1]
                if i < len(entries):
                    e = entries[i]
                    # Join keys with spaces [cite: 26, 41, 55]
                    line = " ".join(str(e.get(k, 0)) for k in VAR_KEYS)
                    str_list.append(line.ljust(128))
                else:
                    # Empty entries are padded blanks [cite: 29-40]
                    str_list.append("".ljust(128))
            
            # Convert 1D list of strings to 2D character array (12, 128)
            v[:] = stringtochar(np.array(str_list, dtype='S128'))

    rootgrp.close()
    print(f"Success: NetCDF created at {nc_file_path}")

# Run script

def SoilMgmtWriter(in_json, out_nc):
    create_netcdf_from_cdl_schema(in_json, out_nc)

# Execute
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python SoilMgmtWriter.py input.json output.nc")
        raise SystemExit(1)

    SoilMgmtWriter(sys.argv[1], sys.argv[2])