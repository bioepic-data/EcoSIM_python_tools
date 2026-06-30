#!/usr/bin/env python3
"""Download CDS ERA5 single-level point time-series data for EcoSIM workflows."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


DEFAULT_DATASET = "reanalysis-era5-single-levels"
TIMESERIES_DATASET = "reanalysis-era5-single-levels-timeseries"
DEFAULT_DATE = "1940-01-01/2025-10-01"
DEFAULT_VARIABLES = [
    "2m_dewpoint_temperature",
    "surface_pressure",
    "surface_solar_radiation_downwards",
    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    value = value.strip(".-")
    return value or "site"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download CDS ERA5 single-level point time-series data."
    )
    parser.add_argument("--lon", type=float, required=True, help="Longitude in [-180, 180].")
    parser.add_argument("--lat", type=float, required=True, help="Latitude in [-90, 90].")
    parser.add_argument("--site-id", default="site", help="Stable site ID for output naming.")
    parser.add_argument("--date", default=DEFAULT_DATE, help="CDS date range, e.g. 1940-01-01/2025-10-01.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="CDS dataset name.")
    parser.add_argument(
        "--request-style",
        choices=["auto", "single-levels", "timeseries"],
        default="auto",
        help="CDS request shape. Auto uses timeseries only for the timeseries dataset short name.",
    )
    parser.add_argument(
        "--credential-format",
        choices=["token", "legacy"],
        default="token",
        help="For environment credentials only: use token for current CDS PATs, or legacy for deprecated UID:key credentials.",
    )
    parser.add_argument(
        "--credential-source",
        choices=["auto", "cdsapirc", "env"],
        default="auto",
        help="Credential source. Auto prefers ~/.cdsapirc, then ERA5_* environment or ~/.bashrc assignments.",
    )
    parser.add_argument("--data-format", default="grib", help="CDS data_format for single-levels requests.")
    parser.add_argument(
        "--area-padding",
        type=float,
        default=0.125,
        help="Degree padding around lon/lat for single-levels area requests.",
    )
    parser.add_argument(
        "--variables",
        nargs="+",
        default=DEFAULT_VARIABLES,
        help="CDS variable names. Defaults to the EcoSIM climate forcing set.",
    )
    parser.add_argument("--output", help="Downloaded data target path.")
    parser.add_argument("--manifest", help="JSON manifest path.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the manifest and print the CDS request without contacting CDS.",
    )
    return parser.parse_args()


def validate_coordinates(lon, lat):
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"longitude {lon} is outside [-180, 180]")
    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"latitude {lat} is outside [-90, 90]")


def date_parts(date_range):
    from datetime import date, timedelta

    start_text, end_text = date_range.split("/", 1) if "/" in date_range else (date_range, date_range)
    start = date.fromisoformat(start_text)
    end = date.fromisoformat(end_text)
    if end < start:
        raise ValueError(f"date end {end} is before start {start}")

    years = set()
    months = set()
    days = set()
    current = start
    while current <= end:
        years.add(f"{current.year:04d}")
        months.add(f"{current.month:02d}")
        days.add(f"{current.day:02d}")
        current += timedelta(days=1)
    return sorted(years), sorted(months), sorted(days)


def request_style(args):
    if args.request_style != "auto":
        return args.request_style
    if args.dataset == TIMESERIES_DATASET:
        return "timeseries"
    return "single-levels"


def build_request(args):
    style = request_style(args)
    if style == "timeseries":
        return {
            "variable": list(args.variables),
            "location": {"longitude": args.lon, "latitude": args.lat},
            "date": [args.date],
        }

    years, months, days = date_parts(args.date)
    pad = max(args.area_padding, 0.0)
    north = min(args.lat + pad, 90.0)
    south = max(args.lat - pad, -90.0)
    west = max(args.lon - pad, -180.0)
    east = min(args.lon + pad, 180.0)
    return {
        "product_type": ["reanalysis"],
        "variable": list(args.variables),
        "year": years,
        "month": months,
        "day": days,
        "time": [f"{hour:02d}:00" for hour in range(24)],
        "data_format": args.data_format,
        "download_format": "unarchived",
        "area": [north, west, south, east],
    }


def default_paths(site_id):
    site = safe_name(site_id)
    output = os.path.join("result", "era5", f"{site}_era5_single_levels_timeseries")
    manifest = f"{output}.manifest.json"
    return output, manifest


def write_manifest(path, payload):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def parse_simple_bashrc_assignment(name):
    bashrc = os.path.expanduser("~/.bashrc")
    if not os.path.exists(bashrc):
        return None
    pattern = re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}=(.*)\s*$")
    try:
        with open(bashrc, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                match = pattern.match(line.rstrip("\n"))
                if not match:
                    continue
                value = match.group(1).strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                return value
    except OSError:
        return None
    return None


def has_cdsapirc():
    path = os.path.expanduser("~/.cdsapirc")
    if not os.path.exists(path):
        return False
    keys = set()
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if ":" in stripped:
                    keys.add(stripped.split(":", 1)[0].strip())
                elif "=" in stripped:
                    keys.add(stripped.split("=", 1)[0].strip())
    except OSError:
        return False
    return {"url", "key"}.issubset(keys)


def credential_values():
    user = os.environ.get("ERA5_USR") or parse_simple_bashrc_assignment("ERA5_USR")
    password = (
        os.environ.get("ERA5_PSSWD")
        or os.environ.get("ERA5_PASSWD")
        or parse_simple_bashrc_assignment("ERA5_PSSWD")
        or parse_simple_bashrc_assignment("ERA5_PASSWD")
    )
    return user, password


def should_use_cdsapirc(credential_source):
    if credential_source == "cdsapirc":
        return True
    return credential_source == "auto" and has_cdsapirc()


def cds_client(cdsapi_module, credential_format, credential_source):
    if should_use_cdsapirc(credential_source):
        return cdsapi_module.Client()

    user, password = credential_values()
    if user and password:
        key = f"{user}:{password}" if credential_format == "legacy" else password
        return cdsapi_module.Client(key=key)
    return cdsapi_module.Client()


def credential_source_label(credential_source):
    if should_use_cdsapirc(credential_source):
        return "~/.cdsapirc"
    if credential_source == "cdsapirc":
        return "~/.cdsapirc requested but missing or incomplete"
    if os.environ.get("ERA5_USR") and os.environ.get("ERA5_PSSWD"):
        return "ERA5_USR/ERA5_PSSWD environment variables"
    if os.environ.get("ERA5_USR") and os.environ.get("ERA5_PASSWD"):
        return "ERA5_USR/ERA5_PASSWD environment variables"
    if parse_simple_bashrc_assignment("ERA5_USR") and parse_simple_bashrc_assignment("ERA5_PSSWD"):
        return "~/.bashrc ERA5_USR/ERA5_PSSWD assignments"
    if parse_simple_bashrc_assignment("ERA5_USR") and parse_simple_bashrc_assignment("ERA5_PASSWD"):
        return "~/.bashrc ERA5_USR/ERA5_PASSWD assignments"
    return "cdsapi default configuration"


def main():
    args = parse_args()
    try:
        validate_coordinates(args.lon, args.lat)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    default_output, default_manifest = default_paths(args.site_id)
    output = args.output or default_output
    manifest = args.manifest or default_manifest
    request = build_request(args)
    manifest_payload = {
        "tool": "era5-cds-point-download",
        "dataset": args.dataset,
        "request_style": request_style(args),
        "request": request,
        "site_id": args.site_id,
        "output": os.path.abspath(output),
        "dry_run": bool(args.dry_run),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "credential_source": credential_source_label(args.credential_source),
        "credential_note": "CDS credential values are never recorded.",
    }

    if args.dry_run:
        write_manifest(manifest, manifest_payload)
        print(json.dumps({"dataset": args.dataset, "request": request}, indent=2))
        print(f"Dry-run manifest written: {manifest}")
        return 0

    try:
        import cdsapi
    except ModuleNotFoundError:
        print(
            "Error: cdsapi is not installed. Install cdsapi and configure CDS credentials "
            "following https://cds.climate.copernicus.eu/how-to-api.",
            file=sys.stderr,
        )
        return 2

    output_dir = os.path.dirname(output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    client = cds_client(cdsapi, args.credential_format, args.credential_source)
    client.retrieve(args.dataset, request, output)
    manifest_payload["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_manifest(manifest, manifest_payload)
    print(f"Downloaded ERA5 point time series: {output}")
    print(f"Manifest written: {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
