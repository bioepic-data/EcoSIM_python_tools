#!/usr/bin/env python3
"""Download and extract NLDAS_FORA0125_H primary point forcing from GES DISC.

The command-line location contract is longitude first, latitude second.
Credentials are accepted for the current HTTP session only and are never
written to outputs.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import getpass
import json
import math
import netrc
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

try:
    import numpy as np
except ImportError:  # pragma: no cover - URL generation does not need numpy.
    np = None


COLLECTION_SHORT_NAME = "NLDAS_FORA0125_H"
COLLECTION_VERSION = "2.0"
COLLECTION_ID = "NLDAS_FORA0125_H_2.0"
ARCHIVE_BASE = "https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/NLDAS_FORA0125_H.2.0"
OPENDAP_BASE = "https://hydro1.gesdisc.eosdis.nasa.gov/opendap/NLDAS/NLDAS_FORA0125_H.2.0"
CMR_COLLECTION_URL = (
    "https://cmr.earthdata.nasa.gov/search/collections.json"
    "?short_name=NLDAS_FORA0125_H&version=2.0"
)
FIRST_CMR_TIME = dt.datetime(1979, 1, 1, 13)
BOUNDING_BOX = {
    "west": -125.0,
    "east": -67.0,
    "south": 25.0,
    "north": 53.0,
}
GRID = {
    "lon0": -124.9375,
    "lat0": 25.0625,
    "dx": 0.125,
    "dy": 0.125,
    "nlon": 464,
    "nlat": 224,
}
ALL_PRIMARY_FILE_A_VARIABLES = [
    "CAPE",
    "CRainf_frac",
    "LWdown",
    "PotEvap",
    "PSurf",
    "Qair",
    "Rainf",
    "SWdown",
    "Tair",
    "Wind_E",
    "Wind_N",
]
ECOSIM_CLIMATE_VARIABLES = [
    "Tair",
    "Wind_E",
    "Wind_N",
    "Rainf",
    "Qair",
    "SWdown",
    "PSurf",
]
ECOSIM_CLIMATE_MAPPING = {
    "TMPH": {"nldas": ["Tair"], "conversion": "Tair K to degC"},
    "WINDH": {"nldas": ["Wind_E", "Wind_N"], "conversion": "sqrt(Wind_E**2 + Wind_N**2), m s-1"},
    "RAINH": {"nldas": ["Rainf"], "conversion": "Rainf kg m-2 per hour is numerically mm h-1"},
    "DWPTH": {"nldas": ["Qair", "PSurf"], "conversion": "vapor pressure from specific humidity and pressure, kPa"},
    "SRADH": {"nldas": ["SWdown"], "conversion": "SWdown W m-2"},
    "PATM": {"nldas": ["PSurf"], "conversion": "PSurf Pa to kPa"},
}
VARIABLE_METADATA = {
    "CAPE": {
        "units": "J kg-1",
        "long_name": "Convective Available Potential Energy",
        "standard_name": None,
    },
    "CRainf_frac": {
        "units": "fraction",
        "long_name": "Fraction of total precipitation that is convective",
        "standard_name": None,
    },
    "LWdown": {
        "units": "W m-2",
        "long_name": "Downward longwave radiation flux at surface",
        "standard_name": None,
    },
    "PotEvap": {
        "units": "kg m-2",
        "long_name": "Potential evaporation",
        "standard_name": None,
    },
    "PSurf": {
        "units": "Pa",
        "long_name": "Surface pressure",
        "standard_name": "surface_air_pressure",
    },
    "Qair": {
        "units": "kg kg-1",
        "long_name": "2-meter above ground specific humidity",
        "standard_name": "specific_humidity",
    },
    "Rainf": {
        "units": "kg m-2",
        "long_name": "Total precipitation",
        "standard_name": None,
    },
    "SWdown": {
        "units": "W m-2",
        "long_name": "Downward shortwave radiation flux at surface",
        "standard_name": None,
    },
    "Tair": {
        "units": "K",
        "long_name": "2-meter above ground temperature",
        "standard_name": "air_temperature",
    },
    "Wind_E": {
        "units": "m s-1",
        "long_name": "10-meter above ground zonal wind speed",
        "standard_name": "eastward_wind",
    },
    "Wind_N": {
        "units": "m s-1",
        "long_name": "10-meter above ground meridional wind speed",
        "standard_name": "northward_wind",
    },
}
NATIVE_VALIDITY_LIMITS = {
    "Tair": {
        "min": 183.15,
        "max": 333.15,
        "units": "K",
        "reason": "Equivalent to -90 to 60 degC.",
    },
    "Wind_E": {
        "min": -75.0,
        "max": 75.0,
        "units": "m s-1",
        "reason": "Broad physical screen for 10 m wind components.",
    },
    "Wind_N": {
        "min": -75.0,
        "max": 75.0,
        "units": "m s-1",
        "reason": "Broad physical screen for 10 m wind components.",
    },
    "Rainf": {
        "min": 0.0,
        "max": 500.0,
        "units": "kg m-2 h-1",
        "reason": "Hourly precipitation accumulation cannot be negative; upper bound is intentionally broad.",
    },
    "Qair": {
        "min": 0.0,
        "max": 0.05,
        "units": "kg kg-1",
        "reason": "Broad physical screen for near-surface specific humidity.",
    },
    "SWdown": {
        "min": 0.0,
        "max": 1400.0,
        "units": "W m-2",
        "reason": "Incident shortwave radiation should be non-negative and below clear-sky extreme values.",
    },
    "PSurf": {
        "min": 50000.0,
        "max": 110000.0,
        "units": "Pa",
        "reason": "Broad physical screen for surface atmospheric pressure.",
    },
    "LWdown": {
        "min": 0.0,
        "max": 800.0,
        "units": "W m-2",
        "reason": "Broad physical screen for downwelling longwave radiation.",
    },
    "PotEvap": {
        "min": 0.0,
        "max": 500.0,
        "units": "kg m-2 h-1",
        "reason": "Hourly potential evaporation accumulation cannot be negative; upper bound is intentionally broad.",
    },
    "CAPE": {
        "min": 0.0,
        "max": 10000.0,
        "units": "J kg-1",
        "reason": "Convective available potential energy cannot be negative.",
    },
    "CRainf_frac": {
        "min": 0.0,
        "max": 1.0,
        "units": "fraction",
        "reason": "Convective-rain fraction must be between 0 and 1.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="download_nldas_fora_point.py",
        description=(
            "Read GES DISC NLDAS_FORA0125_H primary hourly forcing and extract "
            "the nearest grid cell for a lon/lat point."
        )
    )
    parser.add_argument("--lon", type=float, required=True, help="Longitude in decimal degrees, west negative.")
    parser.add_argument("--lat", type=float, required=True, help="Latitude in decimal degrees.")
    parser.add_argument("--start", help="UTC start time: YYYY-MM-DD, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:MM.")
    parser.add_argument("--end", help="UTC end time, inclusive.")
    parser.add_argument(
        "--auto-span",
        choices=("complete-calendar-years", "available-years"),
        help=(
            "Infer UTC span from the GES DISC archive. complete-calendar-years "
            "drops partial first and trailing years; available-years starts at "
            "the first actual product hour and still drops an incomplete trailing year."
        ),
    )
    parser.add_argument(
        "--variables",
        nargs="+",
        help=(
            "Variables to extract. Defaults to the primary File A NLDAS variables needed "
            "for EcoSIM climate forcing: Tair Wind_E Wind_N Rainf Qair SWdown PSurf."
        ),
    )
    parser.add_argument(
        "--variable-set",
        choices=("ecosim-climate", "all-primary-file-a"),
        default="ecosim-climate",
        help="Named native-variable set to use when --variables is omitted.",
    )
    parser.add_argument("--output", help="CSV output path. Defaults under result/nldas_gesdisc_point/.")
    parser.add_argument(
        "--manifest",
        help="JSON manifest path. Defaults to the output CSV name with .manifest.json suffix.",
    )
    parser.add_argument(
        "--download-dir",
        default="result/nldas_gesdisc_point/cache",
        help="Directory for cached hourly NetCDF files when --access-method=https-granule.",
    )
    parser.add_argument(
        "--access-method",
        choices=("opendap-point", "https-granule"),
        default="opendap-point",
        help=(
            "Data access path. opendap-point performs constrained scalar point reads; "
            "https-granule downloads full hourly NetCDF granules before point extraction."
        ),
    )
    parser.add_argument(
        "--username",
        help="Earthdata username for GES DISC access. Overrides USR_NLDAS.",
    )
    parser.add_argument(
        "--password",
        help="Earthdata password for GES DISC access. Overrides PASSWD_NLDAS.",
    )
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt interactively for the Earthdata password if --password is not supplied.",
    )
    parser.add_argument(
        "--netrc-file",
        help="Optional .netrc file to read Earthdata credentials from when CLI/env credentials are absent.",
    )
    parser.add_argument(
        "--credential-profile",
        default=os.path.expanduser("~/.bashrc"),
        help=(
            "Bash profile to source for USR_NLDAS and PASSWD_NLDAS when they are "
            "not already in the process environment. Defaults to ~/.bashrc."
        ),
    )
    parser.add_argument(
        "--no-credential-profile",
        action="store_true",
        help="Do not source --credential-profile for credentials.",
    )
    parser.add_argument(
        "--url-list-only",
        action="store_true",
        help="Write the expected hourly URLs to the manifest and skip downloads/extraction.",
    )
    parser.add_argument(
        "--manifest-url-limit",
        type=int,
        default=10000,
        help=(
            "Maximum number of per-hour URLs to include in the manifest. "
            "Large requests write URL summary fields instead."
        ),
    )
    parser.add_argument(
        "--allow-large-download",
        action="store_true",
        help="Allow requests above --large-download-threshold-hours.",
    )
    parser.add_argument(
        "--large-download-threshold-hours",
        type=int,
        default=2400,
        help="Abort requests above this many hours unless --allow-large-download is supplied.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="For https-granule, download NetCDF files and skip CSV extraction; for opendap-point, fetch point API records and write only a manifest.",
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help=(
            "Keep newly downloaded hourly NetCDF granules after point extraction. "
            "By default, newly downloaded raw granules are removed after the "
            "selected point and variables are extracted."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded files and output CSV.",
    )
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help=(
            "Write outputs even if native-variable validity checks flag out-of-range values. "
            "By default, validity failures make the command exit nonzero after writing the manifest."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="HTTP timeout in seconds per file.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per file after transient HTTP failures.",
    )
    parser.add_argument(
        "--skip-missing-variables",
        action="store_true",
        help="Skip variables absent from a granule instead of failing.",
    )
    return parser.parse_args()


def selected_variables(args: argparse.Namespace) -> Tuple[List[str], str]:
    if args.variables:
        return list(args.variables), "custom"
    if args.variable_set == "all-primary-file-a":
        return list(ALL_PRIMARY_FILE_A_VARIABLES), "all-primary-file-a"
    return list(ECOSIM_CLIMATE_VARIABLES), "ecosim-climate"


def parse_utc_hour(value: str) -> dt.datetime:
    text = value.strip().replace("Z", "")
    if "T" not in text and len(text) == 10:
        text = text + "T00:00"
    elif "T" in text and len(text.split("T", 1)[1]) == 2:
        text = text + ":00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
    if parsed.minute != 0 or parsed.second != 0 or parsed.microsecond != 0:
        raise ValueError(f"NLDAS files are hourly; timestamp is not on an hour boundary: {value}")
    return parsed


def format_utc_hour(value: dt.datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:00:00Z")


def iter_hours(start: dt.datetime, end: dt.datetime) -> Iterable[dt.datetime]:
    if end < start:
        raise ValueError("--end must be greater than or equal to --start")
    current = start
    step = dt.timedelta(hours=1)
    while current <= end:
        yield current
        current += step


def expected_hours_for_year(year: int) -> int:
    start = dt.datetime(year, 1, 1)
    end = dt.datetime(year + 1, 1, 1)
    return int((end - start).total_seconds() // 3600)


def validate_lon_lat(lon: float, lat: float) -> None:
    if not (BOUNDING_BOX["west"] <= lon <= BOUNDING_BOX["east"]):
        raise ValueError(
            f"Longitude {lon} is outside the NLDAS domain "
            f"[{BOUNDING_BOX['west']}, {BOUNDING_BOX['east']}]."
        )
    if not (BOUNDING_BOX["south"] <= lat <= BOUNDING_BOX["north"]):
        raise ValueError(
            f"Latitude {lat} is outside the NLDAS domain "
            f"[{BOUNDING_BOX['south']}, {BOUNDING_BOX['north']}]."
        )


def file_name_for_hour(hour: dt.datetime) -> str:
    return f"{COLLECTION_SHORT_NAME}.A{hour:%Y%m%d}.{hour:%H}00.020.nc"


def file_url_for_hour(hour: dt.datetime) -> str:
    return f"{ARCHIVE_BASE}/{hour:%Y}/{hour:%j}/{file_name_for_hour(hour)}"


def opendap_base_url_for_hour(hour: dt.datetime) -> str:
    return f"{OPENDAP_BASE}/{hour:%Y}/{hour:%j}/{file_name_for_hour(hour)}.ascii"


def fixed_grid_point(lon: float, lat: float) -> Dict[str, object]:
    lon_idx = int(round((lon - GRID["lon0"]) / GRID["dx"]))
    lat_idx = int(round((lat - GRID["lat0"]) / GRID["dy"]))
    lon_idx = min(max(lon_idx, 0), int(GRID["nlon"]) - 1)
    lat_idx = min(max(lat_idx, 0), int(GRID["nlat"]) - 1)
    grid_lon = float(GRID["lon0"] + lon_idx * GRID["dx"])
    grid_lat = float(GRID["lat0"] + lat_idx * GRID["dy"])
    return {
        "lon": grid_lon,
        "lat": grid_lat,
        "lon_index": lon_idx,
        "lat_index": lat_idx,
        "lon_coordinate": "lon",
        "lat_coordinate": "lat",
        "selection_policy": "nearest native NLDAS grid cell to requested lon/lat",
    }


def opendap_point_url_for_hour(hour: dt.datetime, variables: Sequence[str], selected_cell: Dict[str, object]) -> str:
    lon_idx = int(selected_cell["lon_index"])
    lat_idx = int(selected_cell["lat_index"])
    pieces = [
        f"lon[{lon_idx}:1:{lon_idx}]",
        f"lat[{lat_idx}:1:{lat_idx}]",
    ]
    for variable in variables:
        pieces.append(f"{variable}[0:1:0][{lat_idx}:1:{lat_idx}][{lon_idx}:1:{lon_idx}]")
    query = ",".join(pieces)
    return f"{opendap_base_url_for_hour(hour)}?{urllib.parse.quote(query, safe='[]:,_')}"


def archive_listing(opener: urllib.request.OpenerDirector, url: str, timeout: int) -> str:
    with opener.open(urllib.request.Request(url), timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def listed_years(opener: urllib.request.OpenerDirector, timeout: int) -> List[int]:
    html = archive_listing(opener, f"{ARCHIVE_BASE}/", timeout)
    years = sorted({int(match) for match in re.findall(r'href="(\d{4})/"', html)})
    if not years:
        raise RuntimeError(f"No year directories found in {ARCHIVE_BASE}/")
    return years


def hour_exists(
    opener: urllib.request.OpenerDirector,
    hour: dt.datetime,
    username: Optional[str],
    password: Optional[str],
    timeout: int,
) -> bool:
    request = urllib.request.Request(file_url_for_hour(hour), method="HEAD")
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 404, 405}:
            return False
        raise
    except urllib.error.URLError:
        return False


def first_hour_in_year(opener: urllib.request.OpenerDirector, year: int, timeout: int) -> dt.datetime:
    html = archive_listing(opener, f"{ARCHIVE_BASE}/{year}/001/", timeout)
    names = re.findall(rf"{COLLECTION_SHORT_NAME}\.A{year}0101\.(\d{{2}})00\.020\.nc", html)
    if not names:
        raise RuntimeError(f"No hourly files found for {year}-001 in GES DISC archive.")
    return dt.datetime(year, 1, 1, min(int(name) for name in names))


def is_complete_calendar_year(
    opener: urllib.request.OpenerDirector,
    year: int,
    username: Optional[str],
    password: Optional[str],
    timeout: int,
) -> bool:
    first = dt.datetime(year, 1, 1, 0)
    last = dt.datetime(year, 12, 31, 23)
    return hour_exists(opener, first, username, password, timeout) and hour_exists(
        opener, last, username, password, timeout
    )


def infer_auto_span(
    opener: urllib.request.OpenerDirector,
    mode: str,
    username: Optional[str],
    password: Optional[str],
    timeout: int,
) -> Tuple[dt.datetime, dt.datetime, Dict[str, object]]:
    years = listed_years(opener, timeout)
    trailing_year = years[-1]
    first_archive_year = years[0]
    first_available_hour = first_hour_in_year(opener, first_archive_year, timeout)
    if first_available_hour == dt.datetime(first_archive_year, 1, 1, 0):
        first_complete_year = first_archive_year
    else:
        first_complete_year = first_archive_year + 1
    while first_complete_year <= trailing_year and not is_complete_calendar_year(
        opener, first_complete_year, username, password, timeout
    ):
        first_complete_year += 1

    last_complete_year = trailing_year
    while last_complete_year >= first_complete_year and not is_complete_calendar_year(
        opener, last_complete_year, username, password, timeout
    ):
        last_complete_year -= 1
    if last_complete_year < first_complete_year:
        raise RuntimeError("Could not identify any complete calendar years in the NLDAS archive.")

    dropped_trailing_years = [year for year in years if year > last_complete_year]
    if mode == "available-years":
        start = first_available_hour
    else:
        start = dt.datetime(first_complete_year, 1, 1, 0)
    end = dt.datetime(last_complete_year, 12, 31, 23)
    metadata = {
        "mode": mode,
        "archive_years": {"first": first_archive_year, "last": trailing_year, "count": len(years)},
        "first_available_hour_utc": format_utc_hour(first_available_hour),
        "first_complete_calendar_year": first_complete_year,
        "last_complete_calendar_year": last_complete_year,
        "dropped_trailing_incomplete_years": dropped_trailing_years,
        "completion_probe": "first complete-year candidate plus trailing archive years",
        "note": (
            "NLDAS_FORA0125_H begins at 1979-01-01T13:00Z; "
            "complete-calendar-years mode starts at the first full UTC calendar year."
        ),
    }
    return start, end, metadata


def default_output_path(lon: float, lat: float, start: dt.datetime, end: dt.datetime) -> Path:
    safe_lon = f"{lon:.4f}".replace("-", "m").replace(".", "p")
    safe_lat = f"{lat:.4f}".replace("-", "m").replace(".", "p")
    name = f"nldas_fora_point_lon{safe_lon}_lat{safe_lat}_{start:%Y%m%d%H}_{end:%Y%m%d%H}.csv"
    return Path("result/nldas_gesdisc_point") / name


def read_netrc_credentials(netrc_file: str) -> Tuple[Optional[str], Optional[str]]:
    path = Path(netrc_file).expanduser()
    if not path.exists():
        return None, None
    try:
        auth = netrc.netrc(str(path))
    except (OSError, netrc.NetrcParseError):
        return None, None
    for host in ("urs.earthdata.nasa.gov", "hydro1.gesdisc.eosdis.nasa.gov"):
        record = auth.authenticators(host)
        if record:
            return record[0], record[2]
    return None, None


def read_profile_credentials(profile_file: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    path = Path(profile_file).expanduser()
    if not path.exists():
        return None, None, None

    command = (
        'source "$CREDENTIAL_PROFILE" >/dev/null 2>&1; '
        'printf "%s\\0%s\\0" "${USR_NLDAS-}" "${PASSWD_NLDAS-}"'
    )
    env = os.environ.copy()
    env["CREDENTIAL_PROFILE"] = str(path)

    for shell_mode in ("-lc", "-ic"):
        result = subprocess.run(
            ["bash", shell_mode, command],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            check=False,
        )
        if result.returncode != 0 and not result.stdout:
            continue
        parts = result.stdout.split(b"\0")
        if len(parts) < 2:
            continue
        username = parts[0].decode("utf-8") or None
        password = parts[1].decode("utf-8") or None
        if username or password:
            return username, password, f"credential-profile:{path}"
    return None, None, None


def resolve_credentials(args: argparse.Namespace) -> Tuple[Optional[str], Optional[str], str]:
    username = args.username or os.environ.get("USR_NLDAS")
    password = args.password or os.environ.get("PASSWD_NLDAS")
    if args.username or args.password:
        source = "cli"
    elif os.environ.get("USR_NLDAS") or os.environ.get("PASSWD_NLDAS"):
        source = "env:USR_NLDAS/PASSWD_NLDAS"
    else:
        source = "not supplied"
    if (not username or not password) and not args.no_credential_profile and args.credential_profile:
        profile_username, profile_password, profile_source = read_profile_credentials(args.credential_profile)
        username = username or profile_username
        password = password or profile_password
        if profile_source:
            source = profile_source
    if (not username or not password) and args.netrc_file:
        netrc_username, netrc_password = read_netrc_credentials(args.netrc_file)
        username = username or netrc_username
        password = password or netrc_password
        if netrc_username or netrc_password:
            source = "netrc"
    if username and not password and args.prompt_password:
        password = getpass.getpass("Earthdata password: ")
        source = "prompt"
    if not username and not password:
        return None, None, "not supplied"
    if not username or not password:
        raise ValueError("Both Earthdata username and password are required when either credential is supplied.")
    return username, password, source


def validate_time_args(args: argparse.Namespace) -> None:
    if args.auto_span:
        if args.start or args.end:
            raise ValueError("Use either --auto-span or explicit --start/--end, not both.")
        return
    if not args.start or not args.end:
        raise ValueError("Provide --start and --end, or use --auto-span.")


class EarthdataTrustedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Carry Basic auth through the GES DISC to Earthdata redirect chain."""

    allowed_hosts = {
        "hydro1.gesdisc.eosdis.nasa.gov",
        "urs.earthdata.nasa.gov",
    }

    def __init__(self, auth_header: Optional[str]):
        super().__init__()
        self.auth_header = auth_header

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None or not self.auth_header:
            return redirected
        host = urllib.parse.urlparse(newurl).hostname
        if host in self.allowed_hosts:
            redirected.add_header("Authorization", self.auth_header)
        return redirected


def build_opener(username: Optional[str], password: Optional[str]) -> urllib.request.OpenerDirector:
    cookie_jar = http.cookiejar.CookieJar()
    auth_header = None
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        auth_header = f"Basic {token}"
    handlers: List[urllib.request.BaseHandler] = [
        urllib.request.HTTPCookieProcessor(cookie_jar),
        EarthdataTrustedRedirectHandler(auth_header),
    ]
    if username and password:
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        for root in (
            "https://urs.earthdata.nasa.gov",
            "https://hydro1.gesdisc.eosdis.nasa.gov",
        ):
            password_mgr.add_password(None, root, username, password)
        handlers.extend(
            [
                urllib.request.HTTPBasicAuthHandler(password_mgr),
                urllib.request.HTTPDigestAuthHandler(password_mgr),
            ]
        )
    opener = urllib.request.build_opener(*handlers)
    opener.addheaders = [("User-Agent", "EcoSIM-NLDAS-FORA-GESDISC-point-downloader/1.0")]
    return opener


def request_with_optional_basic_auth(
    opener: urllib.request.OpenerDirector,
    url: str,
    username: Optional[str],
    password: Optional[str],
    timeout: int,
) -> urllib.response.addinfourl:
    request = urllib.request.Request(url)
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    return opener.open(request, timeout=timeout)


def download_file(
    opener: urllib.request.OpenerDirector,
    url: str,
    destination: Path,
    username: Optional[str],
    password: Optional[str],
    timeout: int,
    retries: int,
    overwrite: bool,
) -> Dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0 and not overwrite:
        return {
            "url": url,
            "local_path": str(destination),
            "status": "cached",
            "bytes": destination.stat().st_size,
        }

    last_error: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            with request_with_optional_basic_auth(opener, url, username, password, timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                with tempfile.NamedTemporaryFile(delete=False, dir=str(destination.parent)) as tmp:
                    tmp_path = Path(tmp.name)
                    shutil.copyfileobj(response, tmp)
                if destination.suffix == ".nc" and "text/html" in content_type.lower():
                    tmp_path.unlink(missing_ok=True)
                    raise RuntimeError(
                        "GES DISC returned HTML for a NetCDF request. Check Earthdata credentials "
                        "and authorize the NASA GESDISC DATA ARCHIVE application."
                    )
                tmp_path.replace(destination)
                return {
                    "url": url,
                    "local_path": str(destination),
                    "status": "downloaded",
                    "bytes": destination.stat().st_size,
                    "content_type": content_type,
                }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def import_netcdf4():
    try:
        import netCDF4  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Point extraction requires the netCDF4 Python package. "
            "Install it, or rerun with --download-only or --url-list-only."
        ) from exc
    return netCDF4


def require_numpy():
    if np is None:
        raise RuntimeError(
            "Point extraction requires numpy. Install it, or rerun with "
            "--download-only or --url-list-only."
        )
    return np


def get_coord_variable(dataset, candidates: Sequence[str]):
    lower_map = {name.lower(): name for name in dataset.variables}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()], dataset.variables[lower_map[candidate.lower()]]
    raise KeyError(f"Could not find any coordinate variable from {candidates}")


def normalize_longitudes(values: np.ndarray, target_lon: float) -> Tuple[np.ndarray, float]:
    arr = np.asarray(values, dtype=float)
    if np.nanmin(arr) >= 0.0 and target_lon < 0.0:
        return arr, target_lon % 360.0
    return arr, target_lon


def nearest_1d_index(values: np.ndarray, target: float) -> int:
    arr = np.asarray(values, dtype=float)
    return int(np.nanargmin(np.abs(arr - target)))


def nearest_grid_indices(dataset, lon: float, lat: float) -> Tuple[int, int, float, float, str, str]:
    lat_name, lat_var = get_coord_variable(dataset, ("lat", "latitude", "y"))
    lon_name, lon_var = get_coord_variable(dataset, ("lon", "longitude", "x"))
    lat_values = np.asarray(lat_var[:], dtype=float)
    lon_values = np.asarray(lon_var[:], dtype=float)
    lon_values_normalized, target_lon = normalize_longitudes(lon_values, lon)

    if lat_values.ndim == 1 and lon_values.ndim == 1:
        lat_idx = nearest_1d_index(lat_values, lat)
        lon_idx = nearest_1d_index(lon_values_normalized, target_lon)
        return lat_idx, lon_idx, float(lon_values[lon_idx]), float(lat_values[lat_idx]), lon_name, lat_name

    if lat_values.shape != lon_values.shape:
        raise ValueError("2-D latitude and longitude arrays must have the same shape.")
    distance2 = (lat_values - lat) ** 2 + (lon_values_normalized - target_lon) ** 2
    flat_idx = int(np.nanargmin(distance2))
    lat_idx, lon_idx = np.unravel_index(flat_idx, lat_values.shape)
    return lat_idx, lon_idx, float(lon_values[lat_idx, lon_idx]), float(lat_values[lat_idx, lon_idx]), lon_name, lat_name


def scalarize(value) -> Optional[float]:
    arr = np.asarray(value)
    if np.ma.isMaskedArray(arr):
        if bool(np.ma.getmaskarray(arr).all()):
            return None
        arr = np.ma.filled(arr, np.nan)
    if arr.shape == ():
        number = float(arr)
    else:
        number = float(arr.reshape(-1)[0])
    if not math.isfinite(number):
        return None
    return number


def parse_float(text: str) -> Optional[float]:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = float(stripped)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def parse_opendap_ascii(text: str, variables: Sequence[str]) -> Dict[str, Optional[float]]:
    if text.lstrip().startswith("<") or "HTTP Basic: Access denied" in text:
        raise RuntimeError(
            "GES DISC returned an authentication or HTML response for the OPeNDAP point request. "
            "Check Earthdata credentials and authorize the NASA GESDISC DATA ARCHIVE application."
        )

    values: Dict[str, Optional[float]] = {}
    wanted = set(variables)
    for line in text.splitlines():
        if "," not in line:
            continue
        left, right = line.split(",", 1)
        left = left.strip()
        if left == "lon":
            values["grid_lon"] = parse_float(right)
        elif left == "lat":
            values["grid_lat"] = parse_float(right)
        else:
            for variable in wanted:
                if left.startswith(f"{variable}.{variable}["):
                    values[variable] = parse_float(right)
                    break

    missing = [variable for variable in variables if variable not in values]
    if missing:
        raise RuntimeError(f"OPeNDAP point response did not include variables: {', '.join(missing)}")
    return values


def fetch_opendap_point_row(
    opener: urllib.request.OpenerDirector,
    hour: dt.datetime,
    variables: Sequence[str],
    lon: float,
    lat: float,
    selected_cell: Dict[str, object],
    username: Optional[str],
    password: Optional[str],
    timeout: int,
    retries: int,
) -> Tuple[Dict[str, object], Dict[str, object]]:
    url = opendap_point_url_for_hour(hour, variables, selected_cell)
    last_error: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            with request_with_optional_basic_auth(opener, url, username, password, timeout) as response:
                raw = response.read()
                text = raw.decode("utf-8", errors="replace")
            values = parse_opendap_ascii(text, variables)
            grid_lon = values.pop("grid_lon", selected_cell["lon"])
            grid_lat = values.pop("grid_lat", selected_cell["lat"])
            row: Dict[str, object] = {
                "timestamp_utc": hour.strftime("%Y-%m-%dT%H:00:00Z"),
                "requested_lon": lon,
                "requested_lat": lat,
                "grid_lon": grid_lon,
                "grid_lat": grid_lat,
                "source_file": file_name_for_hour(hour),
                "source_url": url,
            }
            row.update(values)
            return row, {
                "timestamp_utc": format_utc_hour(hour),
                "url": url,
                "status": "fetched",
                "bytes": len(raw),
            }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch OPeNDAP point values for {format_utc_hour(hour)}: {last_error}")


def build_variable_index(variable, lon_name: str, lat_name: str, lon_idx: int, lat_idx: int) -> Tuple[int, ...]:
    index: List[int] = []
    for dim in variable.dimensions:
        dim_lower = dim.lower()
        if dim == lon_name or dim_lower in {"lon", "longitude", "x"}:
            index.append(lon_idx)
        elif dim == lat_name or dim_lower in {"lat", "latitude", "y"}:
            index.append(lat_idx)
        elif dim_lower == "time":
            index.append(0)
        elif variable.shape[len(index)] == 1:
            index.append(0)
        else:
            raise ValueError(
                f"Variable {variable.name} has unsupported dimension {dim} "
                f"with size {variable.shape[len(index)]}."
            )
    return tuple(index)


def extract_point_rows(
    files: Sequence[Tuple[dt.datetime, Path, str]],
    variables: Sequence[str],
    lon: float,
    lat: float,
    skip_missing: bool,
) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    netCDF4 = import_netcdf4()
    require_numpy()
    rows: List[Dict[str, object]] = []
    variable_metadata: Dict[str, Dict[str, Optional[str]]] = {}
    selected_cell: Optional[Dict[str, object]] = None

    for hour, path, source_url in files:
        with netCDF4.Dataset(str(path)) as dataset:
            lat_idx, lon_idx, grid_lon, grid_lat, lon_name, lat_name = nearest_grid_indices(dataset, lon, lat)
            if selected_cell is None:
                selected_cell = {
                    "lon": grid_lon,
                    "lat": grid_lat,
                    "lon_index": lon_idx,
                    "lat_index": lat_idx,
                    "lon_coordinate": lon_name,
                    "lat_coordinate": lat_name,
                    "selection_policy": "nearest native NLDAS grid cell to requested lon/lat",
                }

            row: Dict[str, object] = {
                "timestamp_utc": hour.strftime("%Y-%m-%dT%H:00:00Z"),
                "requested_lon": lon,
                "requested_lat": lat,
                "grid_lon": grid_lon,
                "grid_lat": grid_lat,
                "source_file": path.name,
                "source_url": source_url,
            }
            for variable_name in variables:
                if variable_name not in dataset.variables:
                    if skip_missing:
                        row[variable_name] = None
                        continue
                    raise KeyError(f"Variable {variable_name} not found in {path}")
                variable = dataset.variables[variable_name]
                index = build_variable_index(variable, lon_name, lat_name, lon_idx, lat_idx)
                row[variable_name] = scalarize(variable[index])
                variable_metadata.setdefault(
                    variable_name,
                    {
                        "units": getattr(variable, "units", None),
                        "long_name": getattr(variable, "long_name", None),
                        "standard_name": getattr(variable, "standard_name", None),
                    },
                )
            rows.append(row)

    if selected_cell is None:
        raise RuntimeError("No files were available for point extraction.")
    return rows, {"selected_grid_cell": selected_cell, "variables": variable_metadata}


def csv_fieldnames(variables: Sequence[str]) -> List[str]:
    return [
        "timestamp_utc",
        "requested_lon",
        "requested_lat",
        "grid_lon",
        "grid_lat",
        *variables,
        "source_file",
        "source_url",
    ]


def write_csv(rows: Sequence[Dict[str, object]], variables: Sequence[str], output: Path, overwrite: bool) -> None:
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output exists; pass --overwrite to replace it: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fieldnames(variables))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_manifest(manifest: Dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def numeric_value(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def new_validity_state(variables: Sequence[str]) -> Dict[str, object]:
    checks: Dict[str, Dict[str, object]] = {}
    for variable in variables:
        limits = NATIVE_VALIDITY_LIMITS.get(variable)
        if limits is None:
            continue
        checks[variable] = {
            "min_allowed": limits.get("min"),
            "max_allowed": limits.get("max"),
            "allowed_values": limits.get("allowed"),
            "units": limits.get("units"),
            "reason": limits.get("reason"),
            "observed": {"min": None, "max": None, "mean": None},
            "_valid_count": 0,
            "_valid_sum": 0.0,
            "invalid_count": 0,
            "sample_invalid": [],
            "passed": True,
        }
    return {"native": checks}


def update_validity_state(
    state: Dict[str, object],
    row: Dict[str, object],
    sample_count: int = 5,
) -> None:
    checks = state.get("native", {})
    if not isinstance(checks, dict):
        return
    timestamp = row.get("timestamp_utc")
    for variable, check_obj in checks.items():
        if not isinstance(check_obj, dict):
            continue
        value = numeric_value(row.get(variable))
        observed = check_obj["observed"]
        if value is not None and isinstance(observed, dict):
            observed["min"] = value if observed["min"] is None else min(float(observed["min"]), value)
            observed["max"] = value if observed["max"] is None else max(float(observed["max"]), value)
            check_obj["_valid_count"] = int(check_obj["_valid_count"]) + 1
            check_obj["_valid_sum"] = float(check_obj["_valid_sum"]) + value

        invalid = value is None
        allowed = check_obj.get("allowed_values")
        if value is not None and allowed is not None:
            invalid = value not in {float(item) for item in allowed}
        if value is not None and allowed is None:
            minimum = check_obj.get("min_allowed")
            maximum = check_obj.get("max_allowed")
            if minimum is not None and value < float(minimum):
                invalid = True
            if maximum is not None and value > float(maximum):
                invalid = True

        if invalid:
            check_obj["invalid_count"] = int(check_obj["invalid_count"]) + 1
            samples = check_obj["sample_invalid"]
            if isinstance(samples, list) and len(samples) < sample_count:
                sample = {"value": value}
                if timestamp is not None:
                    sample["timestamp_utc"] = timestamp
                samples.append(sample)


def finalize_validity_state(state: Dict[str, object]) -> Dict[str, object]:
    checks = state.get("native", {})
    failed: List[Dict[str, object]] = []
    if isinstance(checks, dict):
        for variable, check_obj in checks.items():
            if not isinstance(check_obj, dict):
                continue
            count = int(check_obj.pop("_valid_count", 0))
            total = float(check_obj.pop("_valid_sum", 0.0))
            observed = check_obj.get("observed")
            if count and isinstance(observed, dict):
                observed["mean"] = total / count
            check_obj["passed"] = int(check_obj.get("invalid_count", 0)) == 0
            if not check_obj["passed"]:
                failed.append(
                    {
                        "group": "native",
                        "variable": variable,
                        "invalid_count": int(check_obj.get("invalid_count", 0)),
                    }
                )
    return {
        "all_passed": not failed,
        "failed": failed,
        "native": checks if isinstance(checks, dict) else {},
    }


def raise_if_invalid(validity: Dict[str, object], manifest_path: Path) -> None:
    if validity.get("all_passed", True):
        return
    failed = ", ".join(
        f"{item['group']}:{item['variable']}({item['invalid_count']})"
        for item in validity.get("failed", [])
        if isinstance(item, dict)
    )
    raise RuntimeError(
        f"NLDAS native-variable validity checks failed: {failed}. "
        f"Inspect {manifest_path} or rerun with --allow-invalid to allow the command to succeed."
    )


def manifest_url_payload(urls: Sequence[Tuple[dt.datetime, str]], limit: int) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "count": len(urls),
        "first": {"timestamp_utc": format_utc_hour(urls[0][0]), "url": urls[0][1]} if urls else None,
        "last": {"timestamp_utc": format_utc_hour(urls[-1][0]), "url": urls[-1][1]} if urls else None,
    }
    if len(urls) <= limit:
        payload["items"] = [{"timestamp_utc": format_utc_hour(hour), "url": url} for hour, url in urls]
    else:
        payload["items_omitted"] = len(urls)
        payload["manifest_url_limit"] = limit
    return payload


def empty_request_payload(total_count: int, limit: int) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "count": total_count,
        "first": None,
        "last": None,
    }
    if total_count <= limit:
        payload["items"] = []
    else:
        payload["items_omitted"] = total_count
        payload["manifest_url_limit"] = limit
    return payload


def note_request_record(payload: Dict[str, object], record: Dict[str, object]) -> None:
    compact = {
        "timestamp_utc": record.get("timestamp_utc"),
        "status": record.get("status"),
        "bytes": record.get("bytes"),
        "url": record.get("url"),
    }
    if payload.get("first") is None:
        payload["first"] = compact
    payload["last"] = compact
    items = payload.get("items")
    if isinstance(items, list):
        items.append(compact)


def remove_new_downloads(downloaded: Sequence[Dict[str, object]]) -> int:
    removed = 0
    for record in downloaded:
        if record.get("status") != "downloaded":
            continue
        local_path = record.get("local_path")
        if not isinstance(local_path, str):
            continue
        path = Path(local_path)
        if path.exists():
            path.unlink()
            removed += 1
            record["removed_after_extraction"] = True
    return removed


def main() -> int:
    args = parse_args()
    variables, variable_set = selected_variables(args)
    validate_lon_lat(args.lon, args.lat)

    username, password, credential_source = resolve_credentials(args)
    opener = build_opener(username, password)

    validate_time_args(args)
    auto_span_metadata: Optional[Dict[str, object]] = None
    if args.auto_span:
        start, end, auto_span_metadata = infer_auto_span(
            opener,
            args.auto_span,
            username,
            password,
            args.timeout,
        )
    else:
        start = parse_utc_hour(args.start)
        end = parse_utc_hour(args.end)

    hours = list(iter_hours(start, end))
    if not hours:
        raise RuntimeError("No hourly timestamps requested.")

    output = Path(args.output) if args.output else default_output_path(args.lon, args.lat, start, end)
    manifest_path = Path(args.manifest) if args.manifest else output.with_suffix(".manifest.json")
    download_dir = Path(args.download_dir)

    selected_cell = fixed_grid_point(args.lon, args.lat)
    if args.access_method == "opendap-point":
        urls = [(hour, opendap_point_url_for_hour(hour, variables, selected_cell)) for hour in hours]
    else:
        urls = [(hour, file_url_for_hour(hour)) for hour in hours]
    manifest: Dict[str, object] = {
        "collection": {
            "short_name": COLLECTION_SHORT_NAME,
            "version": COLLECTION_VERSION,
            "entry_id": COLLECTION_ID,
            "cmr_collection_url": CMR_COLLECTION_URL,
            "archive_base": ARCHIVE_BASE,
            "opendap_base": OPENDAP_BASE,
        },
        "request": {
            "lon": args.lon,
            "lat": args.lat,
            "start_utc": format_utc_hour(start),
            "end_utc": format_utc_hour(end),
            "hour_count": len(hours),
            "variables": variables,
            "variable_set": variable_set,
            "auto_span": auto_span_metadata,
            "access_method": args.access_method,
            "allow_invalid": bool(args.allow_invalid),
        },
        "spatial_extraction_policy": {
            "mode": "point-only",
            "selection": "nearest native NLDAS grid cell to requested lon/lat",
            "requested_coordinate_order": "longitude, latitude",
            "selected_grid_cell_preview": selected_cell,
            "note": (
                "The output CSV rows contain only the selected location and requested variables. "
                "The default opendap-point access method uses constrained scalar reads."
            ),
        },
        "ecosim_climate_mapping": ECOSIM_CLIMATE_MAPPING if variable_set == "ecosim-climate" else None,
        "authentication": {
            "credential_source": credential_source,
            "username_supplied": bool(username),
            "password_supplied": bool(password),
        },
        "urls": manifest_url_payload(urls, args.manifest_url_limit),
        "created_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if args.url_list_only:
        write_manifest(manifest, manifest_path)
        print(f"Wrote URL manifest: {manifest_path}")
        return 0

    if len(hours) > args.large_download_threshold_hours and not args.allow_large_download:
        write_manifest(manifest, manifest_path)
        raise RuntimeError(
            f"Refusing to request {len(hours)} hourly records without --allow-large-download. "
            f"A manifest with the inferred span was written to {manifest_path}."
        )

    if args.access_method == "opendap-point":
        extraction_metadata = {
            "selected_grid_cell": selected_cell,
            "variables": {
                variable: VARIABLE_METADATA.get(
                    variable,
                    {"units": None, "long_name": None, "standard_name": None},
                )
                for variable in variables
            },
            "access_method": "opendap-point",
        }
        api_request_payload = empty_request_payload(len(hours), args.manifest_url_limit)
        validity_state = new_validity_state(variables)
        if args.download_only:
            for hour in hours:
                row, record = fetch_opendap_point_row(
                    opener=opener,
                    hour=hour,
                    variables=variables,
                    lon=args.lon,
                    lat=args.lat,
                    selected_cell=selected_cell,
                    username=username,
                    password=password,
                    timeout=args.timeout,
                    retries=args.retries,
                )
                update_validity_state(validity_state, row)
                note_request_record(api_request_payload, record)
            manifest["api_requests"] = api_request_payload
            manifest["extraction"] = extraction_metadata
            manifest["validity_checks"] = finalize_validity_state(validity_state)
            write_manifest(manifest, manifest_path)
            if not args.allow_invalid:
                raise_if_invalid(manifest["validity_checks"], manifest_path)
            print(f"Fetched {len(hours)} point API records; wrote manifest: {manifest_path}")
            return 0

        if output.exists() and not args.overwrite:
            raise FileExistsError(f"Output exists; pass --overwrite to replace it: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output.with_name(f".{output.name}.tmp")
        try:
            with temp_output.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=csv_fieldnames(variables))
                writer.writeheader()
                for hour in hours:
                    row, record = fetch_opendap_point_row(
                        opener=opener,
                        hour=hour,
                        variables=variables,
                        lon=args.lon,
                        lat=args.lat,
                        selected_cell=selected_cell,
                        username=username,
                        password=password,
                        timeout=args.timeout,
                        retries=args.retries,
                    )
                    writer.writerow(row)
                    update_validity_state(validity_state, row)
                    note_request_record(api_request_payload, record)
            temp_output.replace(output)
        except Exception:
            temp_output.unlink(missing_ok=True)
            raise
        manifest["api_requests"] = api_request_payload
        manifest["extraction"] = extraction_metadata
        manifest["raw_cache_policy"] = {
            "keep_raw": False,
            "note": "No full gridded NetCDF granules were downloaded; OPeNDAP constrained point reads were used.",
        }
        manifest["outputs"] = {"csv": str(output), "manifest": str(manifest_path)}
        manifest["validity_checks"] = finalize_validity_state(validity_state)
        write_manifest(manifest, manifest_path)
        if not args.allow_invalid:
            raise_if_invalid(manifest["validity_checks"], manifest_path)
        print(f"Wrote point CSV: {output}")
        print(f"Wrote manifest: {manifest_path}")
        return 0

    downloaded: List[Dict[str, object]] = []
    files_for_extraction: List[Tuple[dt.datetime, Path, str]] = []
    for hour, url in urls:
        destination = download_dir / f"{hour:%Y}" / f"{hour:%j}" / file_name_for_hour(hour)
        record = download_file(
            opener=opener,
            url=url,
            destination=destination,
            username=username,
            password=password,
            timeout=args.timeout,
            retries=args.retries,
            overwrite=args.overwrite,
        )
        downloaded.append(record)
        files_for_extraction.append((hour, destination, url))

    manifest["files"] = downloaded

    if args.download_only:
        write_manifest(manifest, manifest_path)
        print(f"Downloaded {len(downloaded)} files; wrote manifest: {manifest_path}")
        return 0

    rows, extraction_metadata = extract_point_rows(
        files_for_extraction,
        variables,
        args.lon,
        args.lat,
        args.skip_missing_variables,
    )
    write_csv(rows, variables, output, args.overwrite)
    manifest["extraction"] = extraction_metadata
    validity_state = new_validity_state(variables)
    for row in rows:
        update_validity_state(validity_state, row)
    manifest["validity_checks"] = finalize_validity_state(validity_state)
    if not args.keep_raw:
        removed_count = remove_new_downloads(downloaded)
        manifest["raw_cache_policy"] = {
            "keep_raw": False,
            "removed_new_downloads_after_extraction": removed_count,
            "note": "Point CSV and manifest retain only the selected grid-cell values for requested variables.",
        }
    else:
        manifest["raw_cache_policy"] = {"keep_raw": True}
    manifest["outputs"] = {"csv": str(output), "manifest": str(manifest_path)}
    write_manifest(manifest, manifest_path)
    if not args.allow_invalid:
        raise_if_invalid(manifest["validity_checks"], manifest_path)
    print(f"Wrote point CSV: {output}")
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
