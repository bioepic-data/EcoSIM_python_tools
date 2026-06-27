# NLDAS_FORA0125_H GES DISC API Reference

## Official Links

- Dataset summary: https://disc.gsfc.nasa.gov/datasets/NLDAS_FORA0125_H_2.0/summary?keywords=NLDAS
- CMR collection metadata: https://cmr.earthdata.nasa.gov/search/collections.json?short_name=NLDAS_FORA0125_H&version=2.0
- OPeNDAP endpoint: https://hydro1.gesdisc.eosdis.nasa.gov/opendap/NLDAS/NLDAS_FORA0125_H.2.0/
- HTTPS archive: https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0/
- Collection landing page: https://disc.gsfc.nasa.gov/datacollection/NLDAS_FORA0125_H_2.0.html
- NLDAS documentation PDF: https://docserver.gesdisc.eosdis.nasa.gov/public/project/hydrology/NLDAS2_README.pdf

## Collection Metadata

- Short name: `NLDAS_FORA0125_H`.
- Version: `2.0`.
- Title: `NLDAS Primary Forcing Data L4 Hourly 0.125 x 0.125 degree V2.0`.
- Time coverage starts at `1979-01-01T13:00:00Z`.
- Native cadence is hourly UTC.
- Spatial bounding box is west `-125`, south `25`, east `-67`, north `53`.
- The collection advertises spatial and temporal subsetting through NASA services, but the most stable direct access route is the HTTPS archive file pattern below.
- The archive root listed folders `1979/` through `2026/` on June 26, 2026. Because `2026` is incomplete, the last complete UTC calendar year is `2025`.
- Day `1979/001` starts at `13:00Z`, so the first complete UTC calendar year is `1980`.

## URL Pattern

For constrained point extraction, prefer the OPeNDAP ASCII endpoint and request only the selected lon/lat indices:

```text
https://hydro1.gesdisc.eosdis.nasa.gov/opendap/NLDAS/NLDAS_FORA0125_H.2.0/{YYYY}/{DDD}/NLDAS_FORA0125_H.A{YYYYMMDD}.{HH}00.020.nc.ascii?lon[{i}:1:{i}],lat[{j}:1:{j}],Tair[0:1:0][{j}:1:{j}][{i}:1:{i}],...
```

For the US-UMB site at longitude `-84.7138`, latitude `45.5598`, the nearest native NLDAS grid cell is longitude `-84.6875`, latitude `45.5625` (`lon` index `322`, `lat` index `164`).

For the HTTPS granule fallback, construct:

```text
https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0/{YYYY}/{DDD}/NLDAS_FORA0125_H.A{YYYYMMDD}.{HH}00.020.nc
```

Example:

```text
https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0/2020/001/NLDAS_FORA0125_H.A20200101.0000.020.nc
```

The adjacent `.nc.xml` sidecar provides granule-level metadata and measured parameter names.

## Authentication

GES DISC data access may require Earthdata Login and authorization for the `NASA GESDISC DATA ARCHIVE` application. Support all of these credential paths:

- `--username` and `--password` command-line arguments when the user explicitly wants to pass credentials.
- `USR_NLDAS` and `PASSWD_NLDAS` environment variables for routine scripted use. The bundled script sources `~/.bashrc` by default when those variables are not already visible to the current process.
- A `.netrc`/cookie workflow only when the user explicitly requests it or passes `--netrc-file`.

Do not persist credentials in manifests, shell history notes, logs, or generated scripts.

For scripted OPeNDAP requests through `curl`, the Earthdata redirect chain requires trusted redirect behavior, e.g. `curl -L --location-trusted -u "$USR_NLDAS:$PASSWD_NLDAS" ...`. The bundled Python script implements the equivalent behavior in memory and restricts credential forwarding to the GES DISC and Earthdata hosts.

## Measured Parameters

The `2020/001/NLDAS_FORA0125_H.A20200101.0000.020.nc.xml` sidecar lists:

| Variable | Description | Units |
| --- | --- | --- |
| `CAPE` | Convective Available Potential Energy | `J kg-1` |
| `CRainf_frac` | Fraction of total precipitation that is convective | `fraction` |
| `LWdown` | Downward longwave radiation flux at surface | `W m-2` |
| `PotEvap` | Potential evaporation | `kg m-2` |
| `PSurf` | Surface pressure | `Pa` |
| `Qair` | 2-meter above ground specific humidity | `kg kg-1` |
| `Rainf` | Total precipitation | `kg m-2` |
| `SWdown` | Downward shortwave radiation flux at surface | `W m-2` |
| `Tair` | 2-meter above ground temperature | `K` |
| `Wind_E` | 10-meter above ground zonal wind speed | `m s-1` |
| `Wind_N` | 10-meter above ground meridional wind speed | `m s-1` |

## EcoSIM Climate Subset

For standard EcoSIM climate forcing, extract only the requested location or nearest native NLDAS grid cell, and only:

| EcoSIM target | Native NLDAS inputs | Unit handling |
| --- | --- | --- |
| `TMPH` | `Tair` | K to degC |
| `WINDH` | `Wind_E`, `Wind_N` | scalar speed from vector components |
| `RAINH` | `Rainf` | hourly `kg m-2`, numerically mm water |
| `DWPTH` | `Qair`, `PSurf` | derive vapor pressure in kPa |
| `SRADH` | `SWdown` | W m-2 |
| `PATM` | `PSurf` | Pa to kPa |

Use native units in the first extraction. Convert only in a downstream EcoSIM climate-forcing step unless the user explicitly asks the NLDAS script to be extended into a NetCDF climate writer.
