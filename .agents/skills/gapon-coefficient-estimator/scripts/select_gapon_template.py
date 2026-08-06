#!/usr/bin/env python3
"""Select and depth-map an ecosystem Gapon template for EcoSIM initialization."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_DIR / "assets" / "ecosystem_templates"
DEFAULT_CATALOG = TEMPLATE_ROOT / "template_catalog.csv"
COEFFICIENT_COLUMNS = ("gkc4", "gkch", "gkca", "gkcm", "gkcn", "gkck")
NOTICE = (
    "Gapon coefficients are initialized from the closest ecosystem template, "
    "not derived from site-specific paired exchange and solution chemistry. "
    "They are starting values and are subject to calibration or tuning when needed."
)

FAMILY_KEYWORDS = {
    "peatland": {"peatland", "peat", "bog", "fen"},
    "wetland": {"wetland", "marsh", "swamp", "wet"},
    "rainforest": {"rainforest", "amazon"},
    "tundra": {"tundra", "arctic"},
    "cropland": {
        "cropland", "crop", "agriculture", "agricultural", "maize", "soybean",
        "wheat", "barley", "oat", "canola", "corn", "rotation",
    },
    "pasture": {"pasture", "grazed", "grazing"},
    "grassland": {"grassland", "prairie", "steppe"},
    "forest": {
        "forest", "tree", "woodland", "pine", "spruce", "fir", "oak", "aspen",
        "deciduous", "conifer", "broadleaf", "evergreen",
    },
}

FAMILY_COMPATIBILITY = {
    frozenset(("forest", "rainforest")): 60.0,
    frozenset(("pasture", "grassland")): 65.0,
    frozenset(("wetland", "peatland")): 60.0,
    frozenset(("tundra", "wetland")): 25.0,
    frozenset(("cropland", "pasture")): 20.0,
    frozenset(("cropland", "grassland")): 20.0,
}

GENERIC_TOKENS = {
    "ecosystem", "site", "soil", "natural", "temperate", "warm", "cool", "boreal",
    "arctic", "tropical", "semiarid", "mediterranean", "wet", "dry", "mesic",
}


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    phrase_replacements = {
        "rain-fed": "dryland",
        "rainfed": "dryland",
        "agricultural": "cropland",
        "agriculture": "cropland",
    }
    for old, new in phrase_replacements.items():
        text = text.replace(old, new)
    token_replacements = {"corn": "maize", "soy": "soybean"}
    return " ".join(
        token_replacements.get(token, token)
        for token in re.findall(r"[a-z0-9]+", text)
    )


def tokens(value: str | None) -> set[str]:
    return set(normalize_text(value).split())


def parse_bool(value: str | None) -> bool:
    return normalize_text(value) in {"true", "yes", "1"}


def parse_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"non-finite {label}: {value!r}")
    return number


def load_catalog(path: Path = DEFAULT_CATALOG) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "template_id", "case", "relative_file", "soil_file", "climate", "ecosystem",
        "vegetation", "water_regime", "management", "region", "default_for_case",
    }
    missing = required - set(rows[0] if rows else ())
    if missing:
        raise ValueError(f"template catalog is missing columns: {sorted(missing)}")
    return rows


def infer_family(description: str) -> str | None:
    description_tokens = tokens(description)
    for family in (
        "peatland", "wetland", "rainforest", "tundra", "cropland", "pasture",
        "grassland", "forest",
    ):
        if description_tokens & FAMILY_KEYWORDS[family]:
            return family
    return None


def climate_score(target: str, template: str) -> float:
    target_norm = normalize_text(target)
    template_norm = normalize_text(template)
    if not target_norm:
        return 0.0
    if target_norm == template_norm:
        return 30.0
    target_tokens = tokens(target_norm)
    template_tokens = tokens(template_norm)
    overlap = target_tokens & template_tokens
    if overlap:
        return min(20.0, 10.0 * len(overlap))
    if "temperate" in target_tokens and "temperate" in template_tokens:
        return 8.0
    return 0.0


def score_template(
    row: dict[str, str],
    ecosystem_type: str,
    climate: str = "",
    vegetation: str = "",
    water_regime: str = "",
    management: str = "",
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    target_family = infer_family(" ".join((ecosystem_type, vegetation)))
    template_family = normalize_text(row["ecosystem"])
    if target_family == template_family:
        score += 100.0
        reasons.append("ecosystem_family_exact")
    elif target_family:
        compatibility = FAMILY_COMPATIBILITY.get(
            frozenset((target_family, template_family)), 0.0
        )
        score += compatibility
        if compatibility:
            reasons.append("ecosystem_family_compatible")

    climate_points = climate_score(climate, row["climate"])
    score += climate_points
    if climate_points:
        reasons.append("climate_match")

    target_detail = tokens(" ".join((ecosystem_type, vegetation))) - GENERIC_TOKENS
    template_detail = tokens(" ".join((row["vegetation"], row["case"]))) - GENERIC_TOKENS
    detail_overlap = target_detail & template_detail
    if detail_overlap:
        points = min(32.0, 8.0 * len(detail_overlap))
        score += points
        reasons.append("vegetation_match:" + ",".join(sorted(detail_overlap)))

    target_water = tokens(water_regime)
    template_water = tokens(row["water_regime"])
    if target_water and target_water & template_water:
        score += 15.0
        reasons.append("water_regime_match")

    target_management = tokens(management)
    template_management = tokens(row["management"])
    if target_management and target_management & template_management:
        score += 12.0
        reasons.append("management_match")

    if parse_bool(row["default_for_case"]):
        score += 0.1
    return score, reasons


def rank_templates(
    catalog: list[dict[str, str]],
    ecosystem_type: str,
    climate: str = "",
    vegetation: str = "",
    water_regime: str = "",
    management: str = "",
) -> list[dict[str, object]]:
    ranked = []
    for row in catalog:
        score, reasons = score_template(
            row, ecosystem_type, climate, vegetation, water_regime, management
        )
        ranked.append({"template": row, "score": score, "reasons": reasons})
    return sorted(
        ranked,
        key=lambda item: (-float(item["score"]), str(item["template"]["template_id"])),
    )


def choose_template(
    catalog: list[dict[str, str]],
    template_id: str | None,
    ecosystem_type: str,
    climate: str,
    vegetation: str,
    water_regime: str,
    management: str,
) -> tuple[dict[str, str], list[dict[str, object]]]:
    if template_id:
        matches = [row for row in catalog if row["template_id"] == template_id]
        if not matches:
            raise ValueError(f"unknown template_id {template_id!r}")
        return matches[0], [{"template": matches[0], "score": None, "reasons": ["explicit_template_id"]}]
    if not ecosystem_type:
        raise ValueError("--ecosystem-type is required unless --template-id is provided")
    ranked = rank_templates(
        catalog, ecosystem_type, climate, vegetation, water_regime, management
    )
    if not ranked or float(ranked[0]["score"]) < 100.0:
        raise ValueError(
            "no same-family ecosystem template could be selected; use --template-id to make "
            "an explicit documented choice"
        )
    return ranked[0]["template"], ranked


def load_profile(template: dict[str, str], template_root: Path = TEMPLATE_ROOT) -> list[dict[str, str]]:
    path = template_root / template["relative_file"]
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.DictReader(handle) if row["soil_file"] == template["soil_file"]]
    if not rows:
        raise ValueError(
            f"template profile {template['soil_file']!r} is absent from {template['relative_file']}"
        )
    for row in rows:
        parse_float(row["layer_bottom_depth_m"], "layer_bottom_depth_m")
        for column in COEFFICIENT_COLUMNS:
            parse_float(row[column], column)
    rows.sort(key=lambda row: parse_float(row["layer_bottom_depth_m"], "layer_bottom_depth_m"))
    depths = [parse_float(row["layer_bottom_depth_m"], "layer_bottom_depth_m") for row in rows]
    if any(depth <= 0 for depth in depths) or any(
        depths[index] <= depths[index - 1] for index in range(1, len(depths))
    ):
        raise ValueError(f"template profile depths are not positive and increasing: {depths}")
    return rows


def parse_target_depths(text: str) -> list[float]:
    depths = [parse_float(item.strip(), "target depth") for item in text.split(",") if item.strip()]
    validate_target_depths(depths)
    return depths


def validate_target_depths(depths: list[float]) -> None:
    if not depths:
        raise ValueError("no target depths were provided")
    if any(depth <= 0 for depth in depths):
        raise ValueError("target depths must be positive")
    if any(depths[index] <= depths[index - 1] for index in range(1, len(depths))):
        raise ValueError("target depths must be strictly increasing")


def read_depth_file(path: Path, requested_column: str | None = None) -> list[float]:
    aliases = (
        "layer_bottom_depth_m", "bottom_depth_m", "depth_bottom_m", "depth_m", "botdepz",
    )
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        field_lookup = {normalize_text(name).replace(" ", "_"): name for name in (reader.fieldnames or [])}
        candidates = (requested_column,) if requested_column else aliases
        source_column = None
        for candidate in candidates:
            normalized = normalize_text(candidate).replace(" ", "_")
            if normalized in field_lookup:
                source_column = field_lookup[normalized]
                break
        if source_column is None:
            raise ValueError(
                f"could not find a depth column in {path}; available columns are {reader.fieldnames}"
            )
        depths = [parse_float(row[source_column], source_column) for row in reader]
    validate_target_depths(depths)
    return depths


def depth_map_profile(
    profile: list[dict[str, str]], target_depths: list[float] | None
) -> list[dict[str, object]]:
    if target_depths is None:
        return [
            {
                "layer": row["layer"],
                "layer_bottom_depth_m": parse_float(row["layer_bottom_depth_m"], "depth"),
                "source": row,
                "depth_extended": False,
            }
            for row in profile
        ]

    mapped = []
    source_depths = [parse_float(row["layer_bottom_depth_m"], "depth") for row in profile]
    for layer, target_depth in enumerate(target_depths, start=1):
        source_index = next(
            (index for index, depth in enumerate(source_depths) if depth >= target_depth),
            len(profile) - 1,
        )
        mapped.append(
            {
                "layer": layer,
                "layer_bottom_depth_m": target_depth,
                "source": profile[source_index],
                "depth_extended": target_depth > source_depths[-1],
            }
        )
    return mapped


def output_rows(
    template: dict[str, str], mapped: list[dict[str, object]]
) -> list[dict[str, object]]:
    rows = []
    for item in mapped:
        source = item["source"]
        row: dict[str, object] = {
            "layer": item["layer"],
            "layer_bottom_depth_m": item["layer_bottom_depth_m"],
        }
        row.update({column: source[column] for column in COEFFICIENT_COLUMNS})
        row.update(
            {
                "gapon_source_method": "ecosystem_template_fallback",
                "gapon_template_id": template["template_id"],
                "gapon_template_case": template["case"],
                "gapon_template_soil_file": template["soil_file"],
                "gapon_template_source_layer": source["layer"],
                "gapon_template_source_depth_m": source["layer_bottom_depth_m"],
                "qc_flags": ";".join(
                    flag
                    for flag, active in (
                        ("template_based", True),
                        ("subject_to_tuning", True),
                        ("depth_extended_below_template", bool(item["depth_extended"])),
                    )
                    if active
                ),
            }
        )
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_provenance(
    path: Path,
    template: dict[str, str],
    ranked: list[dict[str, object]],
    args: argparse.Namespace,
    rows: list[dict[str, object]],
) -> None:
    candidates = []
    for item in ranked[:5]:
        candidate = item["template"]
        candidates.append(
            {
                "template_id": candidate["template_id"],
                "case": candidate["case"],
                "soil_file": candidate["soil_file"],
                "score": item["score"],
                "reasons": item["reasons"],
            }
        )
    payload = {
        "method": "ecosystem_template_fallback",
        "template_based": True,
        "subject_to_tuning": True,
        "notice": NOTICE,
        "target": {
            "ecosystem_type": args.ecosystem_type,
            "climate": args.climate,
            "vegetation": args.vegetation,
            "water_regime": args.water_regime,
            "management": args.management,
        },
        "selected_template": {
            "template_id": template["template_id"],
            "case": template["case"],
            "soil_file": template["soil_file"],
            "relative_file": template["relative_file"],
        },
        "selection_candidates": candidates,
        "depth_mapping": [
            {
                "target_layer": row["layer"],
                "target_bottom_depth_m": row["layer_bottom_depth_m"],
                "template_layer": row["gapon_template_source_layer"],
                "template_bottom_depth_m": row["gapon_template_source_depth_m"],
                "depth_extended_below_template": (
                    "depth_extended_below_template" in str(row["qc_flags"])
                ),
            }
            for row in rows
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def list_templates(catalog: list[dict[str, str]]) -> None:
    fields = (
        "template_id", "case", "soil_file", "climate", "ecosystem", "vegetation",
        "water_regime", "management",
    )
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    for row in catalog:
        writer.writerow({field: row[field] for field in fields})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ecosystem-type", default="", help="Target ecosystem or land-use description.")
    parser.add_argument("--climate", default="", help="Target climate class or descriptive climate.")
    parser.add_argument("--vegetation", default="", help="Target vegetation, crop, or dominant species.")
    parser.add_argument("--water-regime", default="", help="Target wet, mesic, dry, or irrigated regime.")
    parser.add_argument("--management", default="", help="Target management such as dryland, irrigated, grazed, or rotation.")
    parser.add_argument("--template-id", help="Explicit template override from --list-templates.")
    parser.add_argument("--target-depths", help="Comma-separated target layer-bottom depths in meters.")
    parser.add_argument("--depth-file", type=Path, help="CSV containing target layer-bottom depths.")
    parser.add_argument("--depth-column", help="Depth column in --depth-file; aliases are detected by default.")
    parser.add_argument("--output", type=Path, help="Output depth-explicit Gapon CSV.")
    parser.add_argument("--provenance-output", type=Path, help="Optional provenance JSON path.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help=argparse.SUPPRESS)
    parser.add_argument("--list-templates", action="store_true", help="List bundled template profiles as CSV.")
    args = parser.parse_args(argv)

    try:
        catalog = load_catalog(args.catalog)
        if args.list_templates:
            list_templates(catalog)
            return 0
        if not args.output:
            parser.error("--output is required unless --list-templates is used")
        if args.target_depths and args.depth_file:
            parser.error("use only one of --target-depths and --depth-file")

        template, ranked = choose_template(
            catalog,
            args.template_id,
            args.ecosystem_type,
            args.climate,
            args.vegetation,
            args.water_regime,
            args.management,
        )
        target_depths = None
        if args.target_depths:
            target_depths = parse_target_depths(args.target_depths)
        elif args.depth_file:
            target_depths = read_depth_file(args.depth_file, args.depth_column)

        profile = load_profile(template, args.catalog.parent)
        mapped = depth_map_profile(profile, target_depths)
        rows = output_rows(template, mapped)
        write_csv(args.output, rows)
        provenance_path = args.provenance_output or args.output.with_suffix(".provenance.json")
        write_provenance(provenance_path, template, ranked, args, rows)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"Selected template {template['template_id']} ({template['case']}; {template['soil_file']})."
    )
    print(f"REMINDER: {NOTICE}")
    print(f"Wrote {args.output} and {provenance_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
