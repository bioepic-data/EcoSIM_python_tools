import rasterio
from pyproj import Transformer
import json
import os
import argparse
import glob
import math

def is_valid_grid_value(ion, value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(value) or value <= -900 or abs(value) >= 1e20:
        return False
    if ion == "phlab":
        return 0.0 <= value <= 14.0
    return value >= 0.0

def extract_nadp_range(lat, lon, base_dir, output_file, start_year, end_year):
    # List of ions to extract
    ions = ["phlab", "so4", "no3", "nh4", "ca", "mg", "na", "k", "cl"]

    # Conversion factors to elemental mass
    elemental_conversions = {
        "so4": 0.3338, "no3": 0.2259, "nh4": 0.7765
    }

    results = {
        "metadata": {
            "requested_lat": lat, "requested_lon": lon,
            "years": list(range(start_year, end_year + 1))
        },
        "data_by_year": {}
    }

    valid_extensions = [".tif", ".asc", ".TIF", ".ASC"]

    for year in range(start_year, end_year + 1):
        year_str = str(year)
        year_root = os.path.join(base_dir, year_str)
        if not os.path.exists(year_root): continue

        year_data = {"raw_ion_conc": {}, "elemental_conc": {}}
        
        for ion in ions:
            folder_variants = ["pH"] if ion == "phlab" else [ion.upper(), ion.capitalize()]
            grid_file = None
            for f_ion in folder_variants:
                sub_folder = f"{f_ion}_conc_{year_str}"
                file_prefix = f"conc_{ion.lower()}_{year_str}"
                for ext in valid_extensions:
                    target_path = os.path.join(year_root, sub_folder, f"{file_prefix}{ext}")
                    if os.path.exists(target_path):
                        grid_file = target_path
                        break
                if grid_file: break
            
            if grid_file:
                try:
                    with rasterio.open(grid_file) as src:
                        # --- CRITICAL FIX: TRANSFORM COORDINATES ---
                        # If the file is not in degrees (EPSG:4326), we must transform
                        if src.crs and not src.crs.is_geographic:
                            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                            target_x, target_y = transformer.transform(lon, lat)
                        else:
                            target_x, target_y = lon, lat

                        # Use index to find the specific pixel row and column
                        row, col = src.index(target_x, target_y)
                        
                        # Verify we are inside the image bounds
                        if 0 <= row < src.height and 0 <= col < src.width:
                            val = src.read(1)[row, col]
                            
                            # Filter out NoData and physically invalid values.
                            if is_valid_grid_value(ion, val):
                                key = "ph" if ion == "phlab" else f"{ion}_mg_l"
                                year_data["raw_ion_conc"][key] = float(val)
                                
                                if ion in elemental_conversions:
                                    element_val = val * elemental_conversions[ion]
                                    element_key = f"{ion}_as_element_mg_l"
                                    year_data["elemental_conc"][element_key] = float(element_val)
                except Exception as e:
                    print(f"  [Error] {year_str} {ion}: {e}")

        results["data_by_year"][year_str] = year_data

    # Save logic
    with open(output_file, 'w') as out:
        json.dump(results, out, indent=4)
    print(f"Extraction complete. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--year1", type=int, required=True)
    parser.add_argument("--year2", type=int, required=True)
    args = parser.parse_args()
    extract_nadp_range(args.latitude, args.longitude, args.input, args.output, args.year1, args.year2)
