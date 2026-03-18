import xarray as xr
import numpy as np

def extract_cams_to_netcdf_vars(nc_file, lat, lon):
    """
    Extracts CAMS EAC4 wet deposition and calculates concentration variables.
    
    Args:
        nc_file (str): Path to CAMS NetCDF file (EAC4).
        lat (float): Target Latitude.
        lon (float): Target Longitude (-180 to 180).
    """
    # Load the dataset
    ds = xr.open_dataset(nc_file)
    
    # Handle CAMS 0-360 longitude convention
    if lon < 0:
        lon_query = 360 + lon
    else:
        lon_query = lon
        
    # Spatial and Temporal aggregation (Mean values for the period)
    site = ds.sel(latitude=lat, longitude=lon_query, method="nearest").mean(dim='time')
    
    # Precipitation Rate (kg m-2 s-1) - 'tp' is often total accumulation; 
    # ensure it is converted to a rate if not already provided as one.
    p_rate = site['tp'].values 
    
    # Helper to calculate concentration (g/m3)
    def get_conc(dep_var):
        if dep_var in site and p_rate > 1e-9: # Avoid division by zero
            return (site[dep_var].values / p_rate) * 1000
        return 0.0

    # Stoichiometric Ratios for Earth's Crust
    AL_RATIO = 0.08   # 8% Aluminum in dust
    FE_RATIO = 0.035  # 3.5% Iron in dust

    # Variable Mapping
    extracted_vars = {
        "CN4RIG": get_conc('wet_deposition_of_ammonium_aerosol'),
        "CNORIG": get_conc('wet_deposition_of_nitrate_aerosol'),
        "CSORG":  get_conc('wet_deposition_of_sulfate_aerosol'),
        "CCLRG":  get_conc('sea_salt_aerosol_wet_deposition'), # Sea salt proxy
        "PHRG":   5.6, # Default background pH; use NADP for local US sites
    }

    # Calculate CALRG and CFERG from Dust
    if 'dust_aerosol_wet_deposition' in site:
        dust_conc = get_conc('dust_aerosol_wet_deposition')
        extracted_vars["CALRG"] = dust_conc * AL_RATIO
        extracted_vars["CFERG"] = dust_conc * FE_RATIO
    else:
        extracted_vars["CALRG"] = 0.0
        extracted_vars["CFERG"] = 0.0

    return extracted_vars

# Example Usage: Blodgett Forest
results = extract_cams_to_netcdf_vars("cams_eac4_data.nc", 38.8953, -120.6328)
print("Extracted Variables for Template:")
for k, v in results.items():
    print(f"{k}: {v:.6f}")
