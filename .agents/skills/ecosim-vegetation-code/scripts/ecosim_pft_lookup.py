#!/usr/bin/env python3
"""Lookup and validate EcoSIM PFT codes from an EcoSIM PFT-parameter CDL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _extract_strings(data_section: str, var_name: str) -> list[str]:
    match = re.search(rf"\n\s*{re.escape(var_name)}\s*=\s*(.*?);", data_section, re.S)
    if not match:
        raise ValueError(f"Could not find data block for {var_name!r}")
    return [item.rstrip() for item in re.findall(r'"([^"]*)"', match.group(1))]


def load_scheme(cdl_path: Path) -> dict[str, object]:
    text = cdl_path.read_text(encoding="utf-8")
    try:
        data_section = text.split("\ndata:", 1)[1]
    except IndexError as exc:
        raise ValueError(f"{cdl_path} does not look like a CDL file with a data section") from exc

    pfts = _extract_strings(data_section, "pfts")
    pft_short = _extract_strings(data_section, "pfts_short")
    pft_long = [value.strip() for value in _extract_strings(data_section, "pfts_long")]
    koppen_no = _extract_strings(data_section, "koppen_clim_no")
    koppen_short = [value.strip() for value in _extract_strings(data_section, "koppen_clim_short")]
    koppen_long = [value.strip() for value in _extract_strings(data_section, "koppen_clim_long")]

    pft_types = [
        {"short": short, "long": long}
        for short, long in zip(pft_short, pft_long)
    ]
    koppen = [
        {"no": no, "short": short, "long": long}
        for no, short, long in zip(koppen_no, koppen_short, koppen_long)
    ]
    available_by_short: dict[str, list[str]] = {}
    for code in pfts:
        available_by_short.setdefault(code[:4], []).append(code)

    return {
        "pfts": pfts,
        "pft_types": pft_types,
        "koppen": koppen,
        "available_by_short": available_by_short,
    }


def resolve_koppen(value: str, koppen: list[dict[str, str]]) -> dict[str, str] | None:
    needle = value.strip().lower()
    for item in koppen:
        if needle == item["no"].lower() or needle == item["short"].lower():
            return item
    return None


def search_pfts(query: str, scheme: dict[str, object]) -> list[dict[str, object]]:
    needle = query.lower()
    available_by_short = scheme["available_by_short"]
    assert isinstance(available_by_short, dict)
    hits = []
    for item in scheme["pft_types"]:
        assert isinstance(item, dict)
        short = str(item["short"])
        long = str(item["long"])
        codes = available_by_short.get(short, [])
        if needle in short.lower() or needle in long.lower() or any(needle in code.lower() for code in codes):
            hits.append({"short": short, "long": long, "available_codes": codes})
    return hits


def print_rows(rows: list[list[str]]) -> None:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdl", default="templates/ecosim_pftpar_20260303.nc.cdl", help="EcoSIM PFT parameter CDL")
    parser.add_argument("--short", help="pfts_short code, e.g. ndlf or gr3s")
    parser.add_argument("--koppen", help="Koppen numerical code or class, e.g. 34 or Csa")
    parser.add_argument("--search", help="Search pfts_short, pfts_long, and available pfts codes")
    parser.add_argument("--list-pfts", action="store_true", help="List pfts_short values and available six-character codes")
    parser.add_argument("--list-koppen", action="store_true", help="List Koppen numerical code mapping")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    scheme = load_scheme(Path(args.cdl))

    if args.list_koppen:
        rows = [["no", "short", "long"]]
        rows += [[item["no"], item["short"], item["long"]] for item in scheme["koppen"]]
        if args.json:
            print(json.dumps(scheme["koppen"], indent=2))
        else:
            print_rows(rows)
        return 0

    if args.list_pfts:
        rows = [["short", "long", "available codes"]]
        available_by_short = scheme["available_by_short"]
        assert isinstance(available_by_short, dict)
        for item in scheme["pft_types"]:
            assert isinstance(item, dict)
            short = str(item["short"])
            rows.append([short, str(item["long"]), ", ".join(available_by_short.get(short, []))])
        if args.json:
            print(json.dumps(search_pfts("", scheme), indent=2))
        else:
            print_rows(rows)
        return 0

    if args.search:
        hits = search_pfts(args.search, scheme)
        if args.json:
            print(json.dumps(hits, indent=2))
        else:
            rows = [["short", "long", "available codes"]]
            rows += [[hit["short"], hit["long"], ", ".join(hit["available_codes"])] for hit in hits]
            print_rows(rows if len(rows) > 1 else [["no matches", "", ""]])
        return 0 if hits else 1

    if args.short and args.koppen:
        short = args.short.strip().lower()
        pft_by_short = {item["short"]: item for item in scheme["pft_types"]}
        if short not in pft_by_short:
            hits = search_pfts(short, scheme)
            print(f"Unknown pfts_short: {short}", file=sys.stderr)
            if hits:
                print(json.dumps(hits, indent=2), file=sys.stderr)
            return 2

        koppen = resolve_koppen(args.koppen, scheme["koppen"])
        if koppen is None:
            print(f"Unknown Koppen code/class: {args.koppen}", file=sys.stderr)
            return 2

        candidate = f"{short}{koppen['no']}"
        pfts = scheme["pfts"]
        available = scheme["available_by_short"].get(short, [])
        result = {
            "candidate": candidate,
            "status": "exact" if candidate in pfts else "missing",
            "pfts_short": short,
            "pfts_long": pft_by_short[short]["long"],
            "koppen": koppen,
            "available_codes_for_short": available,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"candidate: {candidate}")
            print(f"status: {result['status']}")
            print(f"pfts_long: {result['pfts_long']}")
            print(f"koppen: {koppen['no']} {koppen['short']} - {koppen['long']}")
            if result["status"] != "exact":
                print(f"available for {short}: {', '.join(available) if available else '(none)'}")
        return 0 if result["status"] == "exact" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
