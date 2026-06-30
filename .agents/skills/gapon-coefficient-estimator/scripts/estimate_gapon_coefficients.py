#!/usr/bin/env python3
"""Estimate Ca-normalized Gapon selectivity coefficients from CSV data.

The script intentionally refuses to hide data gaps: standard SSURGO/gSSURGO
inputs usually need lab exchangeable bases plus solution chemistry before a
Gapon coefficient can be estimated. Computed values are checked against the
cation adsorption lyotropic prior Al=Fe>Ca>Mg>K=NH4, but are not overwritten.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import sys
from pathlib import Path


LYOTROPIC_SERIES = "Al=Fe>Ca>Mg>K=NH4"

CATIONS = {
    "al": {"charge": 3, "label": "Ca-Al", "lyotropic_rank": 1},
    "fe": {"charge": 3, "label": "Ca-Fe", "lyotropic_rank": 1},
    "mg": {"charge": 2, "label": "Ca-Mg", "lyotropic_rank": 3},
    "k": {"charge": 1, "label": "Ca-K", "lyotropic_rank": 4},
    "nh4": {"charge": 1, "label": "Ca-NH4", "lyotropic_rank": 4},
    "na": {"charge": 1, "label": "Ca-Na"},
    "h": {"charge": 1, "label": "Ca-H"},
}

LYOTROPIC_COMPARISONS = (
    ("al", "mg"),
    ("al", "k"),
    ("al", "nh4"),
    ("fe", "mg"),
    ("fe", "k"),
    ("fe", "nh4"),
    ("mg", "k"),
    ("mg", "nh4"),
)


ALIASES = {
    "exchange_ca": ["exchange_ca_cmolc_kg", "exch_ca", "cax", "ca_x", "caex"],
    "exchange_mg": ["exchange_mg_cmolc_kg", "exch_mg", "mgx", "mg_x", "mgex"],
    "exchange_na": ["exchange_na_cmolc_kg", "exch_na", "nax", "na_x", "naex"],
    "exchange_k": ["exchange_k_cmolc_kg", "exch_k", "kx", "k_x", "kex"],
    "exchange_nh4": ["exchange_nh4_cmolc_kg", "exch_nh4", "nh4x", "nh4_x", "nh4ex"],
    "exchange_al": ["exchange_al_cmolc_kg", "exch_al", "alx", "al_x", "alex", "extral_r"],
    "exchange_fe": ["exchange_fe_cmolc_kg", "exch_fe", "fex", "fe_x", "feex"],
    "exchange_h": ["exchange_h_cmolc_kg", "exch_h", "hx", "h_x", "hex"],
    "exchange_acidity": ["exchange_acidity_cmolc_kg", "extracid_r", "acid_r", "acidity"],
    "cec7": ["cec7_r", "cec7", "cec_cmolc_kg"],
    "ecec": ["ecec_r", "ecec"],
    "ph": ["ph", "ph1to1h2o_r", "ph_h2o"],
}


def normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"na", "nan", "none", "null", "."}:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if not math.isfinite(out):
        return None
    return out


def find_value(row: dict[str, str], key: str) -> float | None:
    names = ALIASES.get(key, [key])
    for name in names:
        value = parse_float(row.get(normalize(name)))
        if value is not None:
            return value
    return None


def solution_value(row: dict[str, str], ion: str) -> tuple[float | None, str | None]:
    candidates = [
        (f"activity_{ion}", "activity"),
        (f"a_{ion}", "activity"),
        (f"solution_{ion}_mol_l", "concentration_as_activity"),
        (f"solution_{ion}_mmol_l", "concentration_as_activity"),
        (f"solution_{ion}_mmolc_l", "concentration_as_activity"),
        (f"{ion}_solution", "concentration_as_activity"),
        (f"{ion}_aq", "concentration_as_activity"),
    ]
    for name, source in candidates:
        value = parse_float(row.get(normalize(name)))
        if value is not None:
            if "_mmol" in name:
                return value / 1000.0, source
            return value, source
    if ion == "h":
        ph = find_value(row, "ph")
        if ph is not None:
            return 10 ** (-ph), "ph_as_h_activity"
    return None, None


def estimate_h_from_acidity(row: dict[str, str], flags: list[str]) -> float | None:
    h = find_value(row, "exchange_h")
    if h is not None:
        return h
    acidity = find_value(row, "exchange_acidity")
    al = find_value(row, "exchange_al") or 0.0
    if acidity is not None:
        flags.append("exchange_h_estimated_from_acidity_minus_al")
        return max(acidity - al, 0.0)
    return None


def estimate_ca(row: dict[str, str], flags: list[str]) -> float | None:
    ca = find_value(row, "exchange_ca")
    if ca is not None:
        return ca

    mg = find_value(row, "exchange_mg") or 0.0
    na = find_value(row, "exchange_na") or 0.0
    k = find_value(row, "exchange_k") or 0.0
    nh4 = find_value(row, "exchange_nh4") or 0.0
    al = find_value(row, "exchange_al") or 0.0
    fe = find_value(row, "exchange_fe") or 0.0
    h = estimate_h_from_acidity(row, flags) or 0.0
    ph = find_value(row, "ph")
    ecec = find_value(row, "ecec")
    cec7 = find_value(row, "cec7")
    base_competitors = mg + na + k + nh4 + fe
    acidic_competitors = base_competitors + al + h

    if ph is not None and ph < 7 and ecec is not None:
        flags.append("exchange_ca_estimated_by_ecec_acidic_closure")
        return ecec - acidic_competitors
    if cec7 is not None:
        flags.append("exchange_ca_estimated_by_cec7_base_closure")
        return cec7 - base_competitors
    if ecec is not None:
        flags.append("exchange_ca_estimated_by_ecec_closure_without_ph")
        return ecec - acidic_competitors
    return None


def add_lyotropic_flags(out: dict[str, str], flags: list[str]) -> None:
    values = {
        ion: parse_float(out.get(f"kg_ca_{ion}"))
        for ion in ("al", "fe", "mg", "k", "nh4")
    }
    for stronger, weaker in LYOTROPIC_COMPARISONS:
        strong_value = values.get(stronger)
        weak_value = values.get(weaker)
        if strong_value is None or weak_value is None:
            continue
        if strong_value < weak_value:
            flags.append(f"possible_lyotropic_inversion_{stronger}_below_{weaker}")


def compute_row(row: dict[str, str], allow_estimate_ca: bool) -> dict[str, str]:
    flags: list[str] = []
    ca_x = estimate_ca(row, flags) if allow_estimate_ca else find_value(row, "exchange_ca")
    ca_a, ca_source = solution_value(row, "ca")
    out: dict[str, str] = {}

    if ca_x is None:
        flags.append("missing_exchange_ca")
    elif ca_x <= 0:
        flags.append("nonpositive_exchange_ca")
    if ca_a is None:
        flags.append("missing_solution_ca")
    elif ca_a <= 0:
        flags.append("nonpositive_solution_ca")
    if ca_source and ca_source != "activity":
        flags.append(f"ca_{ca_source}")

    for ion, meta in CATIONS.items():
        ex = estimate_h_from_acidity(row, flags) if ion == "h" else find_value(row, f"exchange_{ion}")
        aq, aq_source = solution_value(row, ion)
        kg_key = f"kg_ca_{ion}"
        out[kg_key] = ""

        if ex is None:
            flags.append(f"missing_exchange_{ion}")
            continue
        if aq is None:
            flags.append(f"missing_solution_{ion}")
            continue
        if ca_x is None or ca_a is None or ca_x <= 0 or ca_a <= 0 or ex < 0 or aq <= 0:
            flags.append(f"cannot_compute_{ion}")
            continue
        if aq_source and aq_source != "activity":
            flags.append(f"{ion}_{aq_source}")

        z = meta["charge"]
        kg = (ex / ca_x) * (ca_a ** 0.5) / (aq ** (1.0 / z))
        out[kg_key] = f"{kg:.8g}"

    add_lyotropic_flags(out, flags)
    out["lyotropic_series"] = LYOTROPIC_SERIES
    out["exchange_ca_used_cmolc_kg"] = "" if ca_x is None else f"{ca_x:.8g}"
    out["qc_flags"] = ";".join(sorted(set(flags)))
    return out


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{normalize(k): v for k, v in row.items()} for row in reader]


def write_csv(path: Path, input_rows: list[dict[str, str]], computed: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in input_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    for key in ["exchange_ca_used_cmolc_kg", *[f"kg_ca_{ion}" for ion in CATIONS], "lyotropic_series", "qc_flags"]:
        if key not in fieldnames:
            fieldnames.append(key)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for original, extra in zip(input_rows, computed):
            merged = dict(original)
            merged.update(extra)
            writer.writerow(merged)


def self_test() -> int:
    sample = io.StringIO(
        "id,exchange_ca_cmolc_kg,exchange_na_cmolc_kg,exchange_mg_cmolc_kg,"
        "exchange_k_cmolc_kg,exchange_nh4_cmolc_kg,"
        "exchange_al_cmolc_kg,exchange_fe_cmolc_kg,"
        "exchange_acidity_cmolc_kg,activity_ca,activity_na,activity_mg,"
        "activity_k,activity_nh4,activity_al,activity_fe,ph\n"
        "a,4,0.4,1.2,0.2,0.2,0.8,0.8,1.8,"
        "0.0025,0.001,0.0016,0.1,0.1,0.000001,0.000001,5.5\n"
    )
    rows = [{normalize(k): v for k, v in row.items()} for row in csv.DictReader(sample)]
    result = compute_row(rows[0], allow_estimate_ca=True)
    required = ["kg_ca_na", "kg_ca_mg", "kg_ca_k", "kg_ca_nh4", "kg_ca_al", "kg_ca_fe", "kg_ca_h"]
    missing = [key for key in required if not result.get(key)]
    if missing:
        print(f"self-test failed; missing {missing}", file=sys.stderr)
        return 1
    print("self-test ok")
    print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Input CSV with exchange and solution columns.")
    parser.add_argument("--output", type=Path, help="Output CSV with Gapon coefficient columns.")
    parser.add_argument("--estimate-ca", action="store_true", help="Estimate missing exchangeable Ca by flagged CEC/ECEC closure.")
    parser.add_argument("--self-test", action="store_true", help="Run a built-in smoke test.")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.input or not args.output:
        parser.error("--input and --output are required unless --self-test is used")

    rows = read_csv(args.input)
    computed = [compute_row(row, allow_estimate_ca=args.estimate_ca) for row in rows]
    write_csv(args.output, rows, computed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
