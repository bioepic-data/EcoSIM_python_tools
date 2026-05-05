#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


HEADER_RE = re.compile(
    r"PLANT traits for FUNCTIONAL TYPE\s*\((?P<dims>[^)]+)\)\s*=\s*(?P<indices>.+?)\s+(?P<code>[A-Za-z0-9_.-]+)\s*$"
)
CLASS_RE = re.compile(
    r"^(?P<item>\d+)\|\s*(?P<code>[A-Za-z0-9]+)\s*:\s*(?P<desc>.+?)\s*:\s*(?P<value>.+)$"
)
TRAIT_RE = re.compile(
    r"^(?P<item>\d+)\s*:\s*(?P<code>[A-Za-z0-9]+)\s*\|\s*(?P<desc>.+?)\s*:\s*(?P<value>.+)$"
)
META_RE = re.compile(r"^(?P<key>.+?)\s*:\s*(?P<value>.+)$")
SECTION_RE = re.compile(r"^[A-Z][A-Z &/()_-]+$")


def parse_scalar(value: str):
    value = value.strip()
    number = value.replace("D", "E").replace("d", "E")
    try:
        return float(number)
    except ValueError:
        return value


def normalize_trait(section: str, item_no: str, code: str, desc: str, raw_value: str):
    unit = ""
    description = desc.strip()
    unit_match = re.match(r"^(.*?)\s*\[([^\]]+)\]\s*$", description)
    if unit_match:
        description = unit_match.group(1).strip()
        unit = unit_match.group(2).strip()

    value = raw_value.strip()
    parsed = parse_scalar(value)
    return {
        "section": section,
        "item_no": int(item_no),
        "code": code.strip(),
        "description": description,
        "unit": unit,
        "raw_value": value,
        "numeric_value": parsed if isinstance(parsed, float) else None,
        "value": parsed,
    }


def parse_desc(text: str):
    blocks = []
    current = None
    current_section = None

    for raw_line in text.splitlines():
        line = raw_line.replace("\t", " ").rstrip()
        stripped = line.strip()

        if not stripped:
            continue
        if re.fullmatch(r"[-=]{10,}", stripped):
            continue

        header_match = HEADER_RE.match(stripped)
        if header_match:
            if current:
                blocks.append(current)
            current = {
                "functional_type_code": header_match.group("code").strip(),
                "dimensions": header_match.group("dims").strip(),
                "indices": header_match.group("indices").strip(),
                "plant_name": "",
                "koppen_climate_info": "",
                "traits": [],
            }
            current_section = None
            continue

        if current is None:
            continue

        if SECTION_RE.match(stripped):
            current_section = stripped
            continue

        meta_match = META_RE.match(stripped)
        if meta_match and current_section is None:
            key = meta_match.group("key").strip().lower()
            value = meta_match.group("value").strip()
            if key.startswith("plant name"):
                current["plant_name"] = value
                continue
            if key.startswith("koppen climate info"):
                current["koppen_climate_info"] = value
                continue

        class_match = CLASS_RE.match(stripped)
        if class_match and current_section:
            current["traits"].append(
                normalize_trait(
                    current_section,
                    class_match.group("item"),
                    class_match.group("code"),
                    class_match.group("desc"),
                    class_match.group("value"),
                )
            )
            continue

        trait_match = TRAIT_RE.match(stripped)
        if trait_match and current_section:
            current["traits"].append(
                normalize_trait(
                    current_section,
                    trait_match.group("item"),
                    trait_match.group("code"),
                    trait_match.group("desc"),
                    trait_match.group("value"),
                )
            )

    if current:
        blocks.append(current)

    return blocks


def build_profile(block: dict):
    by_code = {}
    by_section = {}

    for trait in block["traits"]:
        entry = {
            "section": trait["section"],
            "item_no": trait["item_no"],
            "description": trait["description"],
            "unit": trait["unit"],
            "value": trait["value"],
            "raw_value": trait["raw_value"],
        }
        existing = by_code.get(trait["code"])
        if existing is None:
            by_code[trait["code"]] = entry
        elif isinstance(existing, list):
            existing.append(entry)
        else:
            by_code[trait["code"]] = [existing, entry]
        by_section.setdefault(trait["section"], []).append(trait)

    return {
        "functional_type_code": block["functional_type_code"],
        "plant_name": block["plant_name"],
        "koppen_climate_info": block["koppen_climate_info"],
        "trait_count": len(block["traits"]),
        "traits_by_code": by_code,
        "traits_by_section": by_section,
    }


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: extract_trait_profiles.py /absolute/path/to/plant_trait.desc",
            file=sys.stderr,
        )
        raise SystemExit(2)

    source = Path(sys.argv[1]).expanduser().resolve()
    text = source.read_text(encoding="utf-8")
    blocks = parse_desc(text)

    block_by_code = {block["functional_type_code"]: block for block in blocks}
    missing = [code for code in ("ndlf43", "gr3s43") if code not in block_by_code]
    if missing:
        raise SystemExit(f"Missing required functional type block(s): {', '.join(missing)}")

    payload = {
        "source_file": str(source),
        "available_functional_types": [block["functional_type_code"] for block in blocks],
        "tree_profile": build_profile(block_by_code["ndlf43"]),
        "grass_profile": build_profile(block_by_code["gr3s43"]),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
