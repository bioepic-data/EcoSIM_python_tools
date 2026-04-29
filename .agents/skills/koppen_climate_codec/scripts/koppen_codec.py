#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys

KOPPEN_DATA = {
    "11": "Af",
    "12": "Am",
    "13": "As",
    "14": "Aw",
    "21": "BWk",
    "22": "BWh",
    "26": "BSk",
    "27": "BSh",
    "31": "Cfa",
    "32": "Cfb",
    "33": "Cfc",
    "34": "Csa",
    "35": "Csb",
    "36": "Csc",
    "37": "Cwa",
    "38": "Cwb",
    "39": "Cwc",
    "41": "Dfa",
    "42": "Dfb",
    "43": "Dfc",
    "44": "Dfd",
    "45": "Dsa",
    "46": "Dsb",
    "47": "Dsc",
    "48": "Dsd",
    "49": "Dwa",
    "50": "Dwb",
    "51": "Dwc",
    "52": "Dwd",
    "61": "ET",
    "62": "EF",
}

LETTER_TO_NUMERIC = {v.upper(): k for k, v in KOPPEN_DATA.items()}


def normalize_letter_code(value: str) -> str:
    candidate = value.strip()
    numeric = LETTER_TO_NUMERIC.get(candidate.upper())
    if numeric is None:
        raise KeyError(candidate)
    return KOPPEN_DATA[numeric]


def validate_coordinates(latitude: float | None, longitude: float | None) -> None:
    if latitude is None and longitude is None:
        return
    if latitude is None or longitude is None:
        raise ValueError("Both latitude and longitude must be provided together.")
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Latitude out of range: {latitude}")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Longitude out of range: {longitude}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert between Koppen letter codes and numeric codes."
    )
    parser.add_argument("--letter", help="Koppen letter code such as Csa or Dfb.")
    parser.add_argument("--numeric", help="Koppen numeric code such as 34 or 42.")
    parser.add_argument("--latitude", type=float, help="Optional latitude for output context.")
    parser.add_argument("--longitude", type=float, help="Optional longitude for output context.")
    parser.add_argument(
        "--lookup-source",
        default="manual",
        help="Optional lookup source label, such as web_lookup or ameriflux_metadata.",
    )
    parser.add_argument(
        "--confidence-note",
        default="conversion only",
        help="Optional confidence note to include in the output payload.",
    )
    args = parser.parse_args()

    if bool(args.letter) == bool(args.numeric):
        print("Provide exactly one of --letter or --numeric.", file=sys.stderr)
        return 2

    try:
        validate_coordinates(args.latitude, args.longitude)
        if args.letter:
            koppen_letter_code = normalize_letter_code(args.letter)
            koppen_numeric_code = LETTER_TO_NUMERIC[koppen_letter_code.upper()]
        else:
            koppen_numeric_code = args.numeric.strip()
            koppen_letter_code = KOPPEN_DATA[koppen_numeric_code]
    except KeyError as exc:
        print(f"Unknown Koppen code: {exc.args[0]}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "koppen_letter_code": koppen_letter_code,
        "koppen_numeric_code": koppen_numeric_code,
        "lookup_source": args.lookup_source,
        "confidence_note": args.confidence_note,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
