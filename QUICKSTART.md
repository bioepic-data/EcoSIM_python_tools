# Quick Start: EcoSIM Grid Forcing

## Installation

```bash
# Install required packages
pip install netCDF4 numpy pandas rasterio pyproj shapely pyogrio geopandas requests matplotlib playwright

# Optional local vision setup for bundled scripts
ollama pull qwen2.5vl:7b
```

The site metadata step reads an AmeriFlux site page screenshot to recover latitude, longitude, elevation, mean annual temperature, climate class, and vegetation type. If your agent already has vision capabilities, or if you use a hosted multimodal model, you can use that instead of local Ollama. The bundled CLI scripts default to an Ollama-compatible local endpoint.

To use a different local Ollama-compatible model or endpoint:
```bash
export OLLAMA_VISION_MODEL=qwen2.5vl:7b
export OLLAMA_API_URL=http://localhost:11434/api/chat
```

## Usage

### Single Site
```bash
python create_ecosim_grid_forcing.py US-Ha1
```

### Multiple Sites
```bash
python create_ecosim_grid_forcing.py US-Ha1
python create_ecosim_grid_forcing.py US-Ha3
python create_ecosim_grid_forcing.py US-MMS
```

### In a Loop
```bash
for site in US-Ha1 US-Ha3 US-MMS US-Blk US-AR1; do
  python create_ecosim_grid_forcing.py $site
done
```

## Output

For each site, you get:

- **`result/<SITE_ID>_ecosim_grid.nc`** ← Main output for EcoSIM
- `result/<SITE_ID>_ecosim_site.json` (site metadata)
- `result/profile_<SITE_ID>.json` (soil data)

## Verify Output

```bash
# Check file is valid NetCDF
ncdump -h result/US-Ha1_ecosim_grid.nc | head -20

# List all variables
ncdump -h result/US-Ha1_ecosim_grid.nc | grep "float\|int\|byte"

# Quick Python check
python -c "import netCDF4; ds = netCDF4.Dataset('result/US-Ha1_ecosim_grid.nc'); print('Variables:', len(ds.variables)); print('Dimensions:', dict(ds.dimensions))"
```

## What Gets Extracted

| From | Variable | Units | Source |
|------|----------|-------|--------|
| AmeriFlux | Latitude (ALATG) | °N | Vision AI extraction |
| AmeriFlux | Longitude (ALONG) | °E | Vision AI extraction |
| AmeriFlux | Elevation (ALTIG) | m | Vision AI extraction |
| AmeriFlux | MAT (ATCAG) | °C | Vision AI extraction |
| AmeriFlux | Climate (IETYPG) | Code | Koppen-Geiger mapping |
| AmeriFlux | Vegetation (IXTYP1) | Code | IGBP mapping |
| gSSURGO | Soil depth (CDPTH) | m | Horizon boundaries |
| gSSURGO | Bulk density (BKDSI) | Mg/m³ | Soil property |
| gSSURGO | Field capacity (FC) | m³/m³ | Water retention |
| gSSURGO | Wilting point (WP) | m³/m³ | Water retention |
| gSSURGO | Sand/silt (CSAND/CSILT) | kg/Mg | Texture |
| gSSURGO | pH | unitless | Soil chemistry |
| gSSURGO | CEC | cmol/kg | Exchange capacity |
| gSSURGO | Organic C (CORGC) | kg/Mg | Organic matter |
| Template | All others | varies | Default values |

## Common Issues

### "ModuleNotFoundError: No module named 'netCDF4'"
```bash
pip install netCDF4
```

### "Extracting site information..." hangs
If you are using the bundled local script, confirm the local vision backend is running:
```bash
# In separate terminal
ollama serve

# Then run script again
```

If you are using an agent with native vision or a hosted multimodal API, skip Ollama and provide or capture the AmeriFlux site screenshot for direct metadata extraction.

### "No MUPOLYGON features found"
- Site is outside CONUS
- Check site coordinates are correct
- gSSURGO may not have coverage for that location

### Incomplete soil data
- gSSURGO may not cover entire soil profile
- Missing fields use -999.9 fill value
- This is normal; EcoSIM can handle it

## File Locations

```
result/
├── US-Ha1_ecosim_grid.nc        ← Use this for EcoSIM
├── US-Ha1_ecosim_site.json      ← Site metadata  
├── profile_US-Ha1.json          ← Soil data
├── US-Ha3_ecosim_grid.nc
├── US-Ha3_ecosim_site.json
├── profile_US-Ha3.json
└── ... (more sites)
```

## Performance Tips

- **First run**: 30-60 seconds (fetching data)
- **Subsequent runs**: 2-5 seconds (using cached data)
- **Delete caches to refresh**: `rm result/*_site.json result/profile_*.json`

## Next Steps

1. **Generate files**: Run script for your sites
2. **Verify output**: Check NetCDF structure  
3. **Use in EcoSIM**: Point EcoSIM to `.nc` file as grid input
4. **Configure climate**: Add climate forcing files separately
5. **Run simulation**: EcoSIM will read grid + climate for simulation

## Reference

- Full documentation: See `GRID_FORCING_README.md`
- Implementation details: See `GRID_FORCING_IMPLEMENTATION.md`
- Skills: See `.agents/skills/*/SKILL.md`

---

**Ready to go!** Run `python create_ecosim_grid_forcing.py US-Ha1` to create your first grid file.
