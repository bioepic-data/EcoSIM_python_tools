# ECOSIM NetCDF Generator

This script generates NetCDF input files for the ECOSIM biogeochemical model using:
1. YAML configuration specifying site name and output file
2. Data from the ameriflux_site_info skill for site metadata
3. Data from the ameriflux_atmchem_info skill for atmospheric chemistry
4. The Blodget.clim.2012-2022.nc.template as the NetCDF file structure

## Usage

```bash
python generate_ecosim_netcdf.py config.yaml
```

## Configuration File Format

The YAML configuration file should contain:
- `site_name`: AmeriFlux site identifier (e.g., "US-Ha1")
- `output_file`: Path where the NetCDF file will be saved
- `tdep_data_path`: Path to tDEP data directory
- `start_year`: Starting year for atmospheric chemistry data
- `end_year`: Ending year for atmospheric chemistry data

## Example Configuration

```yaml
site_name: "US-Ha1"
output_file: "result/ecosim_input.nc"
tdep_data_path: "data/tDEP"
start_year: 2012
end_year: 2022
```

## Features

- Integrates with existing AmeriFlux skills
- Uses template-based NetCDF structure
- Handles site metadata extraction
- Extracts atmospheric chemistry data for specified years
- Creates properly formatted ECOSIM input files