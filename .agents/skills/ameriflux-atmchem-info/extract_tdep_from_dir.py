import rasterio
import json
import os
import argparse
from pyproj import Transformer

def extract_tdep_range(lat, lon, base_dir, output_file, start_year, end_year):
    """
    Extracts tDEP variables for a range of years where each year is in its 
    own sub-folder (e.g., base_dir/tDEP-2000/).
    """
    var_mapping = {
        "CN4RIG": "nh4_ww",
        "CNORIG": "no3_ww",
        "CSORG":  "s_ww",
        "CCARG":  "ca_ww",
        "CMGRG":  "mg_ww",
        "CNARG":  "na_ww",
        "CKARG":  "k_ww",
        "CCLRG":  "cl_ww",
        "RAINH":  "precip_ww"
    }

    # Manually define the tDEP Albers Projection
    tdep_crs_string = (
        "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 "
        "+x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
    )

    results = {
        "metadata": {
            "requested_lat": lat,
            "requested_lon": lon,
            "years": list(range(start_year, end_year + 1))
        },
        "data_by_year": {}
    }

    try:
        transformer = Transformer.from_crs("EPSG:4326", tdep_crs_string, always_xy=True)
        target_x, target_y = transformer.transform(lon, lat)
    except Exception as e:
        print(f"Error initializing transformation: {e}")
        return

    for year in range(start_year, end_year + 1):
        year_str = str(year)
        # Define the specific sub-folder for this year
        year_dir = os.path.join(base_dir, f"tDEP-{year_str}")
        
        if not os.path.exists(year_dir):
            print(f"Warning: Directory {year_dir} not found. Skipping year {year_str}.")
            continue

        year_data = {"raw_values": {}, "converted_concentrations": {}}
        files_in_dir = os.listdir(year_dir)
        
        # 1. Extract Precipitation for the specific year
        precip_file = next((f for f in files_in_dir 
                          if f.startswith("precip_ww") and f.endswith('.tif')), None)
        
        precip_m = None
        if precip_file:
            with rasterio.open(os.path.join(year_dir, precip_file)) as src_p:
                precip_val = next(src_p.sample([(target_x, target_y)]))[0]
                if 0 <= precip_val < 1e10:
                    year_data["raw_values"]["RAINH"] = float(precip_val)
                    precip_m = precip_val / 100.0  # cm to meters

        # 2. Extract Chemical Species for the specific year
        for template_var, tdep_prefix in var_mapping.items():
            if template_var == "RAINH": continue
            
            target_file = next((f for f in files_in_dir 
                              if f.startswith(tdep_prefix) and f.endswith('.tif')), None)
            
            if target_file:
                with rasterio.open(os.path.join(year_dir, target_file)) as src:
                    dep_kg_ha = next(src.sample([(target_x, target_y)]))[0]
                    year_data["raw_values"][template_var] = float(dep_kg_ha)
                    
                    if precip_m and precip_m > 0:
                        # Convert kg/ha to g/m^3
                        conc = (dep_kg_ha * 0.1) / precip_m
                        year_data["converted_concentrations"][template_var] = float(conc)
        
        results["data_by_year"][year_str] = year_data

    # Save to JSON
    # 1. Convert to absolute path to avoid "." or "" issues
    abs_output_path = os.path.abspath(output_file)
    output_dir = os.path.dirname(abs_output_path)

    # 2. Now create the directory
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)     
           
    with open(output_file, 'w') as out:
        json.dump(results, out, indent=4)
    
    print(f"Extraction for {start_year}-{end_year} complete. Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract tDEP time-series from year-specific folders.")
    parser.add_argument("--input", required=True, help="Base directory (e.g., data/tDEP/)")
    parser.add_argument("--output", required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--year1", type=int, required=True)
    parser.add_argument("--year2", type=int, required=True)
    
    args = parser.parse_args()
    extract_tdep_range(args.latitude, args.longitude, args.input, args.output, args.year1, args.year2)

if __name__ == "__main__":
    main()