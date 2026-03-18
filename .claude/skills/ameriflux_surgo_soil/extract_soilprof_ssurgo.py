import geopandas as gpd
import pandas as pd
import numpy as np

def generate_20_layer_profiles(site_list, gpkg_path, output_csv="ameriflux_soil_profiles.csv"):
    """
    site_list: List of dicts with {'id': 'US-Bl8', 'lat': 38.89, 'lon': -120.63}
    gpkg_path: Path to your local ALL_SSURGO.gpkg file
    """
    all_site_data = []
    
    # Define the 20 target depths (m) required by the nlevs dimension
    # Adjust the endpoint or distribution to match your specific model grid
    target_depths = np.linspace(0.05, 2.0, 20) 

    for site in site_list:
        print(f"--- Processing Site: {site['id']} ---")
        
        # 1. Spatial Intersection (EPSG:4326)
        point = gpd.points_from_xy([site['lon']], [site['lat']], crs="EPSG:4326")
        try:
            # Use a mask to avoid loading the entire global GeoPackage into RAM
            poly = gpd.read_file(gpkg_path, layer='mupolygon', mask=point)
            if poly.empty:
                print(f"Warning: No spatial match for {site['id']}. Skipping.")
                continue
            mukey = poly['mukey'].iloc[0]
        except Exception as e:
            print(f"Spatial Error for {site['id']}: {e}")
            continue

        # 2. Local Table Joins
        # Get the major component (the dominant soil type)
        cp = gpd.read_file(gpkg_path, layer='component', where=f"mukey='{mukey}'")
        if cp.empty: continue
        
        # Filter for the representative/major component
        maj_cp = cp[cp['majcompflag'] == 'Yes']
        if maj_cp.empty:
            maj_cp = cp.iloc[[0]] # Fallback to first component if no major flag
        
        cokey = maj_cp['cokey'].iloc[0]
        
        # Get horizons associated with this component
        horizons = gpd.read_file(gpkg_path, layer='chorizon', where=f"cokey='{cokey}'")
        horizons = horizons.sort_values('hzdept_r') # Ensure vertical order

        # 3. Vertical Extrapolation (Step C) 
        site_profile = []
        for d in target_depths:
            # Convert depth to cm for gSSURGO comparison
            d_cm = d * 100
            
            # Find the horizon layer that contains this specific depth
            match = horizons[(horizons['hzdept_r'] <= d_cm) & (horizons['hzdepb_r'] >= d_cm)]
            
            if match.empty:
                # Extrapolation: Use the properties of the deepest available horizon 
                row = horizons.iloc[-1]
            else:
                row = match.iloc[0]

            # 4. Map Variables & Unit Conversions [cite: 52-93]
            layer_data = {
                "site_id": site['id'],
                "nlev": len(site_profile) + 1,
                "depth_m": d,
                "CDPTH": row['hzdepb_r'] / 100.0 if pd.notnull(row['hzdepb_r']) else -999.9,  # [cite: 52]
                "BKDSI": row['dbthirdbar_r'] if pd.notnull(row['dbthirdbar_r']) else -999.9, # [cite: 53]
                "SCNV": row['ksat_r'] * 3.6 if pd.notnull(row['ksat_r']) else -999.9,        # 
                "CSAND": row['sandtotal_r'] * 10 if pd.notnull(row['sandtotal_r']) else -999.9, # [cite: 59]
                "ROCK": row['fragvol_r'] / 100.0 if pd.notnull(row['fragvol_r']) else 0.0,  # [cite: 62]
                "PH": row['ph1to1h2o_r'] if pd.notnull(row['ph1to1h2o_r']) else -999.9,     # [cite: 64]
                "CEC": row['cec7_r'] if pd.notnull(row['cec7_r']) else -999.9,              # [cite: 65]
                "CORGC": (row['om_r'] / 1.724) * 10 if pd.notnull(row['om_r']) else -999.9   # 
            }
            site_profile.append(layer_data)
        
        all_site_data.extend(site_profile)

    # Export to CSV for inspection or NetCDF ingestion
    df = pd.DataFrame(all_site_data)
    df.to_csv(output_csv, index=False)
    print(f"SUCCESS: {output_csv} generated.")

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    my_sites = [
        {'id': 'US-Bl8', 'lat': 38.8953, 'lon': -120.6328},
        {'id': 'US-Vcm', 'lat': 35.8884, 'lon': -106.5321}
    ]
    # generate_20_layer_profiles(my_sites, "ALL_SSURGO.gpkg")
