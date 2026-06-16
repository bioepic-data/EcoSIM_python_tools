#!/usr/bin/env python3
"""Convert EcoSIM grid NetCDF files to editable Excel workbooks and back."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import netCDF4 as nc
import numpy as np


CONTROL_SHEET = "control"
DIMENSIONS_SHEET = "dimensions"
GLOBAL_ATTRS_SHEET = "global_attrs"
VARIABLES_SHEET = "variables"
VARIABLE_ATTRS_SHEET = "variable_attrs"
VALUES_SHEET = "values"

CONTROL_COLUMNS = ["key", "value"]
DIMENSION_COLUMNS = ["name", "length", "isunlimited"]
GLOBAL_ATTR_COLUMNS = ["attr", "type", "value"]
VARIABLE_COLUMNS = ["name", "dtype", "dimensions", "fill_value_type", "fill_value"]
VARIABLE_ATTR_COLUMNS = ["variable", "attr", "type", "value"]
VALUE_COLUMNS = ["variable", "linear_index", "indices", "value"]


def clean_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def text_value(value: Any) -> str:
    value = clean_value(value)
    if value is None:
        return ""
    return str(value).strip()


def int_value(value: Any, field: str) -> int:
    text = text_value(value)
    if text == "":
        raise ValueError(f"Missing integer value for {field}")
    return int(float(text))


def bool_value(value: Any) -> bool:
    text = text_value(value).lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n", ""}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def encode_metadata_value(value: Any) -> tuple[str, Any]:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bytes):
        return "str", value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return "str", value
    if isinstance(value, bool):
        return "bool", int(value)
    if isinstance(value, (int, np.integer)):
        return "int", int(value)
    if isinstance(value, (float, np.floating)):
        return "float", float(value)
    if isinstance(value, np.ndarray):
        return "json", json.dumps(value.tolist())
    if isinstance(value, (list, tuple)):
        return "json", json.dumps(list(value))
    return "str", str(value)


def decode_metadata_value(value_type: Any, value: Any) -> Any:
    kind = text_value(value_type).lower()
    if kind == "":
        return None
    if kind == "str":
        return "" if value is None else str(clean_value(value))
    if kind == "int":
        return int_value(value, "metadata value")
    if kind == "float":
        return float(text_value(value))
    if kind == "bool":
        return bool_value(value)
    if kind == "json":
        return json.loads(str(clean_value(value)))
    raise ValueError(f"Unknown metadata value type: {value_type!r}")


def data_value_to_cell(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return clean_value(value)


def cell_to_data_value(value: Any, dtype: np.dtype) -> Any:
    if dtype.kind in {"f"}:
        return float(text_value(value))
    if dtype.kind in {"i", "u"}:
        return int_value(value, "data value")
    if dtype.kind == "b":
        return bool_value(value)
    if dtype.kind in {"S", "a"}:
        text = "" if value is None else str(clean_value(value))
        return text.encode("utf-8")
    return "" if value is None else str(clean_value(value))


def variable_data(var: nc.Variable) -> np.ndarray:
    var.set_auto_maskandscale(False)
    if var.shape == ():
        return np.asarray(var[()])
    return np.asarray(var[:])


def nc_to_sheet_rows(path: Path) -> dict[str, list[list[Any]]]:
    with nc.Dataset(path) as ds:
        sheets: dict[str, list[list[Any]]] = {
            CONTROL_SHEET: [CONTROL_COLUMNS, ["data_model", ds.data_model]],
            DIMENSIONS_SHEET: [DIMENSION_COLUMNS],
            GLOBAL_ATTRS_SHEET: [GLOBAL_ATTR_COLUMNS],
            VARIABLES_SHEET: [VARIABLE_COLUMNS],
            VARIABLE_ATTRS_SHEET: [VARIABLE_ATTR_COLUMNS],
            VALUES_SHEET: [VALUE_COLUMNS],
        }

        for name, dim in ds.dimensions.items():
            sheets[DIMENSIONS_SHEET].append([name, len(dim), int(dim.isunlimited())])

        for attr in ds.ncattrs():
            value_type, value = encode_metadata_value(ds.getncattr(attr))
            sheets[GLOBAL_ATTRS_SHEET].append([attr, value_type, value])

        for name, var in ds.variables.items():
            fill_type = ""
            fill_value = ""
            if "_FillValue" in var.ncattrs():
                fill_type, fill_value = encode_metadata_value(var.getncattr("_FillValue"))
            dims = ",".join(var.dimensions)
            sheets[VARIABLES_SHEET].append([name, str(var.dtype), dims, fill_type, fill_value])

            for attr in var.ncattrs():
                if attr == "_FillValue":
                    continue
                value_type, value = encode_metadata_value(var.getncattr(attr))
                sheets[VARIABLE_ATTRS_SHEET].append([name, attr, value_type, value])

            data = variable_data(var)
            if data.shape == ():
                sheets[VALUES_SHEET].append([name, 0, "", data_value_to_cell(data.item())])
                continue
            for linear_index, index in enumerate(np.ndindex(data.shape)):
                value = data[index]
                sheets[VALUES_SHEET].append(
                    [
                        name,
                        linear_index,
                        ",".join(str(i) for i in index),
                        data_value_to_cell(value),
                    ]
                )

        return sheets


def rows_to_dicts(rows: list[list[Any]], sheet: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    headers = [text_value(h) for h in rows[0]]
    if not headers:
        raise ValueError(f"Sheet {sheet!r} has no header row")
    out = []
    for row in rows[1:]:
        if not any(text_value(v) for v in row):
            continue
        out.append({headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))})
    return out


def sheet_rows_to_nc(sheets: dict[str, list[list[Any]]], path: Path, output_format: str | None = None) -> None:
    for required in [CONTROL_SHEET, DIMENSIONS_SHEET, VARIABLES_SHEET, VALUES_SHEET]:
        if required not in sheets:
            raise ValueError(f"Workbook is missing required sheet: {required}")

    control = {text_value(r.get("key")): r.get("value", "") for r in rows_to_dicts(sheets[CONTROL_SHEET], CONTROL_SHEET)}
    data_model = output_format or text_value(control.get("data_model")) or "NETCDF3_CLASSIC"

    dimensions = rows_to_dicts(sheets[DIMENSIONS_SHEET], DIMENSIONS_SHEET)
    variables = rows_to_dicts(sheets[VARIABLES_SHEET], VARIABLES_SHEET)
    global_attrs = rows_to_dicts(sheets.get(GLOBAL_ATTRS_SHEET, []), GLOBAL_ATTRS_SHEET)
    variable_attrs = rows_to_dicts(sheets.get(VARIABLE_ATTRS_SHEET, []), VARIABLE_ATTRS_SHEET)
    values = rows_to_dicts(sheets[VALUES_SHEET], VALUES_SHEET)

    attrs_by_var: dict[str, list[dict[str, Any]]] = {}
    for row in variable_attrs:
        attrs_by_var.setdefault(text_value(row.get("variable")), []).append(row)

    values_by_var: dict[str, list[dict[str, Any]]] = {}
    for row in values:
        values_by_var.setdefault(text_value(row.get("variable")), []).append(row)

    with nc.Dataset(path, "w", format=data_model) as ds:
        for row in dimensions:
            name = text_value(row.get("name"))
            if not name:
                continue
            length = int_value(row.get("length"), f"dimension {name} length")
            ds.createDimension(name, None if bool_value(row.get("isunlimited", 0)) else length)

        for row in global_attrs:
            attr = text_value(row.get("attr"))
            if attr:
                ds.setncattr(attr, decode_metadata_value(row.get("type"), row.get("value")))

        for row in variables:
            name = text_value(row.get("name"))
            if not name:
                continue
            dtype = np.dtype(text_value(row.get("dtype")))
            dims = tuple(d for d in text_value(row.get("dimensions")).split(",") if d)
            fill_value = None
            if text_value(row.get("fill_value_type")):
                fill_value = decode_metadata_value(row.get("fill_value_type"), row.get("fill_value"))
            var = ds.createVariable(name, dtype, dims, fill_value=fill_value)

            for attr_row in attrs_by_var.get(name, []):
                attr = text_value(attr_row.get("attr"))
                if attr:
                    var.setncattr(attr, decode_metadata_value(attr_row.get("type"), attr_row.get("value")))

            shape = tuple(len(ds.dimensions[d]) for d in dims)
            var_rows = sorted(values_by_var.get(name, []), key=lambda r: int_value(r.get("linear_index", 0), "linear_index"))
            if not dims:
                if var_rows:
                    var.assignValue(cell_to_data_value(var_rows[0].get("value"), dtype))
                continue

            if fill_value is not None:
                data = np.full(shape, fill_value, dtype=dtype)
            else:
                data = np.zeros(shape, dtype=dtype)

            for value_row in var_rows:
                index_text = text_value(value_row.get("indices"))
                if not index_text:
                    continue
                index = tuple(int(part) for part in index_text.split(","))
                data[index] = cell_to_data_value(value_row.get("value"), dtype)
            var[:] = data


def col_name(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def cell_ref(row: int, col: int) -> str:
    return f"{col_name(col)}{row + 1}"


def sheet_xml(rows: list[list[Any]]) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>',
    ]
    for r_idx, row in enumerate(rows):
        out.append(f'<row r="{r_idx + 1}">')
        for c_idx, raw in enumerate(row):
            value = clean_value(raw)
            ref = cell_ref(r_idx, c_idx)
            if value == "" or value is None:
                out.append(f'<c r="{ref}"/>')
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                out.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                text = str(value)
                space = ' xml:space="preserve"' if text != text.strip() or "\n" in text else ""
                out.append(f'<c r="{ref}" t="inlineStr"><is><t{space}>{escape(text)}</t></is></c>')
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def safe_sheet_name(name: str) -> str:
    return re.sub(r"[][/*?:\\\\]", "_", name)[:31] or "Sheet"


def write_xlsx(path: Path, sheets: dict[str, list[list[Any]]]) -> None:
    safe_names = [safe_sheet_name(name) for name in sheets]
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for i in range(len(sheets)):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    workbook = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>',
    ]
    for i, name in enumerate(safe_names, start=1):
        workbook.append(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
    workbook.append("</sheets></workbook>")

    workbook_rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for i in range(len(sheets)):
        workbook_rels.append(
            f'<Relationship Id="rId{i + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i + 1}.xml"/>'
        )
    workbook_rels.append(
        f'<Relationship Id="rId{len(sheets) + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    workbook_rels.append("</Relationships>")

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        "</styleSheet>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "".join(content_types))
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", "".join(workbook))
        zf.writestr("xl/_rels/workbook.xml.rels", "".join(workbook_rels))
        zf.writestr("xl/styles.xml", styles)
        for i, (_, rows) in enumerate(sheets.items(), start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


def ns_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings = []
    for si in root:
        if ns_name(si.tag) != "si":
            continue
        strings.append("".join(t.text or "" for t in si.iter() if ns_name(t.tag) == "t"))
    return strings


def rel_targets(zf: zipfile.ZipFile) -> dict[str, str]:
    root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    out = {}
    for rel in root:
        if ns_name(rel.tag) == "Relationship":
            target = rel.attrib["Target"]
            out[rel.attrib["Id"]] = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
    return out


def cell_col_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha()).upper()
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch) - 64
    return value - 1


def read_cell(cell: ET.Element, shared_strings: list[str]) -> Any:
    ctype = cell.attrib.get("t", "")
    if ctype == "inlineStr":
        return "".join(t.text or "" for t in cell.iter() if ns_name(t.tag) == "t")
    value_el = next((x for x in cell if ns_name(x.tag) == "v"), None)
    if value_el is None or value_el.text is None:
        return ""
    value = value_el.text
    if ctype == "s":
        return shared_strings[int(value)]
    if ctype == "b":
        return int(value) == 1
    try:
        f = float(value)
        return int(f) if f.is_integer() else f
    except ValueError:
        return value


def read_xlsx(path: Path) -> dict[str, list[list[Any]]]:
    with zipfile.ZipFile(path) as zf:
        shared_strings = read_shared_strings(zf)
        targets = rel_targets(zf)
        workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets: dict[str, list[list[Any]]] = {}
        for sheet in workbook_root.iter():
            if ns_name(sheet.tag) != "sheet":
                continue
            name = sheet.attrib["name"]
            rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = targets[rid]
            root = ET.fromstring(zf.read(target))
            rows: list[list[Any]] = []
            for row in root.iter():
                if ns_name(row.tag) != "row":
                    continue
                row_values: list[Any] = []
                for cell in row:
                    if ns_name(cell.tag) != "c":
                        continue
                    col = cell_col_index(cell.attrib.get("r", f"A{len(rows) + 1}"))
                    while len(row_values) <= col:
                        row_values.append("")
                    row_values[col] = read_cell(cell, shared_strings)
                while row_values and row_values[-1] == "":
                    row_values.pop()
                rows.append(row_values)
            sheets[name] = rows
        return sheets


def cmd_nc_to_xlsx(args: argparse.Namespace) -> None:
    write_xlsx(Path(args.output), nc_to_sheet_rows(Path(args.input)))


def cmd_xlsx_to_nc(args: argparse.Namespace) -> None:
    sheet_rows_to_nc(read_xlsx(Path(args.input)), Path(args.output), args.format)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("nc-to-xlsx", help="Export grid NetCDF to an editable Excel workbook")
    p.add_argument("input", help="Input EcoSIM grid NetCDF")
    p.add_argument("output", help="Output .xlsx workbook")
    p.set_defaults(func=cmd_nc_to_xlsx)

    p = sub.add_parser("xlsx-to-nc", help="Rebuild grid NetCDF from an edited workbook")
    p.add_argument("input", help="Input .xlsx workbook")
    p.add_argument("output", help="Output EcoSIM grid NetCDF")
    p.add_argument("--format", help="Override output NetCDF format, e.g. NETCDF3_CLASSIC")
    p.set_defaults(func=cmd_xlsx_to_nc)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
