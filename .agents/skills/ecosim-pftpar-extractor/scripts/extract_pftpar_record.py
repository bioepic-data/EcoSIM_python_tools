#!/usr/bin/env python3
"""Extract one EcoSIM PFT parameter record into a standalone NetCDF file."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, chartostring


PFT_DIM = "npfts"


def decode_char_strings(values: np.ndarray) -> list[str]:
    """Decode NetCDF S1 character arrays or string arrays into stripped text."""
    arr = np.asarray(values)
    if arr.dtype.kind in {"S", "U"} and arr.ndim >= 2:
        return [str(item).strip() for item in chartostring(arr)]
    if arr.dtype.kind in {"S", "U", "O"}:
        return [
            item.decode("utf-8").strip() if isinstance(item, bytes) else str(item).strip()
            for item in arr.ravel()
        ]
    raise TypeError("PFT code variable must be a character or string array")


def find_pft_codes(ds: Dataset) -> list[str]:
    if "pfts" not in ds.variables:
        raise KeyError("Input NetCDF does not contain required variable 'pfts'")
    return decode_char_strings(ds.variables["pfts"][:])


def normalize_code(value: str) -> str:
    return value.strip().lower()


def choose_pft_index(codes: list[str], requested: str, koppen_code: str | None) -> tuple[int, str]:
    request = normalize_code(requested)
    normalized = [normalize_code(code) for code in codes]

    if koppen_code:
        suffix = koppen_code.strip()
        if not re.fullmatch(r"\d{2}", suffix):
            raise ValueError(f"--koppen-code must be two digits, got {koppen_code!r}")
        if len(request) == 4:
            request = f"{request}{suffix}"
        elif len(request) == 6 and not request.endswith(suffix):
            raise ValueError(f"Requested PFT {requested!r} does not match --koppen-code {suffix!r}")

    exact = [i for i, code in enumerate(normalized) if code == request]
    if len(exact) == 1:
        return exact[0], codes[exact[0]].strip()

    if len(request) == 4:
        prefix_hits = [i for i, code in enumerate(normalized) if code.startswith(request)]
        if len(prefix_hits) == 1:
            return prefix_hits[0], codes[prefix_hits[0]].strip()
        if prefix_hits:
            available = ", ".join(codes[i].strip() for i in prefix_hits)
            raise ValueError(
                f"PFT short name {requested!r} is ambiguous; provide --koppen-code. "
                f"Available codes: {available}"
            )

    prefix = request[:4]
    available = [code.strip() for code in codes if normalize_code(code).startswith(prefix)]
    if available:
        raise ValueError(f"PFT {requested!r} not found. Available codes with prefix {prefix!r}: {', '.join(available)}")
    raise ValueError(f"PFT {requested!r} not found in pfts")


def safe_output_name(pft_code: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", pft_code.strip())
    if not safe:
        raise ValueError("Selected PFT code is empty after filename sanitization")
    return f"{safe}.nc"


def copy_dimensions(src: Dataset, dst: Dataset) -> None:
    for name, dim in src.dimensions.items():
        if name == PFT_DIM:
            dst.createDimension(name, None if dim.isunlimited() else 1)
        else:
            dst.createDimension(name, None if dim.isunlimited() else len(dim))


def create_variable_like(src_var, dst: Dataset):
    fill_value = src_var.getncattr("_FillValue") if "_FillValue" in src_var.ncattrs() else None
    kwargs = {}
    if fill_value is not None:
        kwargs["fill_value"] = fill_value
    dst_var = dst.createVariable(src_var.name, src_var.datatype, src_var.dimensions, **kwargs)
    attrs = {attr: src_var.getncattr(attr) for attr in src_var.ncattrs() if attr != "_FillValue"}
    if attrs:
        dst_var.setncatts(attrs)
    return dst_var


def copy_variable(src_var, dst_var, selected_index: int) -> None:
    data = src_var[...]
    if PFT_DIM in src_var.dimensions:
        axis = src_var.dimensions.index(PFT_DIM)
        data = np.take(data, [selected_index], axis=axis)
    dst_var[...] = data


def add_history(dst: Dataset, src_path: Path, pft_code: str, pft_index: int) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"{now}: extracted PFT {pft_code} from {src_path} "
        f"source npfts index {pft_index}"
    )
    prior = getattr(dst, "history", "")
    dst.history = f"{prior}\n{entry}".strip() if prior else entry
    dst.source_pftpar_file = str(src_path)
    dst.selected_pft_code = pft_code
    dst.selected_pft_index_zero_based = pft_index


def extract_record(input_path: Path, output_path: Path, requested: str, koppen_code: str | None, overwrite: bool) -> dict[str, str]:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}. Use --overwrite to replace it.")

    with Dataset(input_path, "r") as src:
        codes = find_pft_codes(src)
        selected_index, selected_code = choose_pft_index(codes, requested, koppen_code)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with Dataset(output_path, "w", format=src.data_model) as dst:
            dst.setncatts({attr: src.getncattr(attr) for attr in src.ncattrs()})
            copy_dimensions(src, dst)
            for name, src_var in src.variables.items():
                dst_var = create_variable_like(src_var, dst)
                copy_variable(src_var, dst_var, selected_index)
            add_history(dst, input_path, selected_code, selected_index)

    with Dataset(output_path, "r") as check:
        out_codes = find_pft_codes(check)
        return {
            "output": str(output_path),
            "selected_pft": out_codes[0] if out_codes else selected_code,
            "npfts": str(len(check.dimensions[PFT_DIM])),
            "variables": str(len(check.variables)),
            "npft_metadata": str(len(check.dimensions["npft"])) if "npft" in check.dimensions else "missing",
            "koppen_metadata": str(len(check.dimensions["nkopenclms"])) if "nkopenclms" in check.dimensions else "missing",
        }


def list_codes(input_path: Path) -> int:
    with Dataset(input_path, "r") as ds:
        for code in find_pft_codes(ds):
            print(code)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Source EcoSIM PFT parameter NetCDF.")
    parser.add_argument("--pft", help="Six-character PFT code such as ndlf34, or four-character short code with --koppen-code.")
    parser.add_argument("--koppen-code", help="Two-digit EcoSIM Koppen climate code when --pft is a short code.")
    parser.add_argument("--output", type=Path, help="Exact output NetCDF path. Defaults to <output-dir>/<selected-pft>.nc.")
    parser.add_argument("--output-dir", type=Path, default=Path("result/pftpar_extracts"), help="Output directory when --output is omitted.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file.")
    parser.add_argument("--list-pfts", action="store_true", help="List available six-character PFT codes and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_pfts:
        return list_codes(args.input)
    if not args.pft:
        parser.error("--pft is required unless --list-pfts is used")

    try:
        with Dataset(args.input, "r") as ds:
            codes = find_pft_codes(ds)
            _, selected_code = choose_pft_index(codes, args.pft, args.koppen_code)
        output = args.output or (args.output_dir / safe_output_name(selected_code))
        summary = extract_record(args.input, output, args.pft, args.koppen_code, args.overwrite)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("Extracted EcoSIM PFT parameter record")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
