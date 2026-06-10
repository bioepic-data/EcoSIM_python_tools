#!/usr/bin/env python3
"""Extract EcoSIM history output variables from Fortran hist_addfld calls."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


STRING_QUOTES = {"'", '"'}
DEFAULT_CALL_REGEX = r"hist_addfld\w*"


def strip_fortran_comment(line: str) -> str:
    """Remove comments that start outside string literals."""
    out: List[str] = []
    quote: Optional[str] = None
    i = 0
    while i < len(line):
        char = line[i]
        if quote:
            out.append(char)
            if char == quote:
                if i + 1 < len(line) and line[i + 1] == quote:
                    out.append(line[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char in STRING_QUOTES:
            quote = char
            out.append(char)
            i += 1
            continue
        if char == "!":
            break
        out.append(char)
        i += 1
    return "".join(out)


def strip_continuation(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r"^\s*&\s*", "", stripped)
    stripped = re.sub(r"\s*&\s*$", "", stripped)
    return stripped


def normalized_source_line(raw: str) -> str:
    return strip_continuation(strip_fortran_comment(raw))


def paren_delta(text: str) -> int:
    quote: Optional[str] = None
    delta = 0
    i = 0
    while i < len(text):
        char = text[i]
        if quote:
            if char == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char in STRING_QUOTES:
            quote = char
        elif char == "(":
            delta += 1
        elif char == ")":
            delta -= 1
        i += 1
    return delta


def split_top_level(text: str, delimiter: str) -> List[str]:
    parts: List[str] = []
    quote: Optional[str] = None
    depth = 0
    start = 0
    i = 0
    while i < len(text):
        char = text[i]
        if quote:
            if char == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char in STRING_QUOTES:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and text.startswith(delimiter, i):
            parts.append(text[start:i].strip())
            i += len(delimiter)
            start = i
            continue
        i += 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def split_named_arg(text: str) -> Tuple[Optional[str], str]:
    quote: Optional[str] = None
    depth = 0
    i = 0
    while i < len(text):
        char = text[i]
        if quote:
            if char == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char in STRING_QUOTES:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "=" and depth == 0:
            return text[:i].strip().lower(), text[i + 1 :].strip()
        i += 1
    return None, text.strip()


def parse_fortran_string(expr: str) -> Optional[str]:
    expr = expr.strip()
    if len(expr) < 2 or expr[0] not in STRING_QUOTES:
        return None
    quote = expr[0]
    if expr[-1] != quote:
        return None
    value: List[str] = []
    i = 1
    while i < len(expr) - 1:
        char = expr[i]
        if char == quote and i + 1 < len(expr) - 1 and expr[i + 1] == quote:
            value.append(quote)
            i += 2
            continue
        if char == quote:
            return None
        value.append(char)
        i += 1
    return "".join(value)


def compact_expr(expr: Optional[str]) -> str:
    if expr is None:
        return ""
    return re.sub(r"\s+", " ", expr.strip())


def expr_to_template(expr: Optional[str]) -> str:
    if not expr:
        return ""
    expr = compact_expr(expr)
    literal = parse_fortran_string(expr)
    if literal is not None:
        return literal
    parts = split_top_level(expr, "//")
    if len(parts) == 1:
        return expr
    rendered: List[str] = []
    for part in parts:
        literal_part = parse_fortran_string(part)
        if literal_part is not None:
            rendered.append(literal_part)
        else:
            rendered.append("{" + compact_expr(part) + "}")
    return "".join(rendered)


def parse_call_text(call_text: str) -> Tuple[str, Dict[str, str]]:
    match = re.search(r"\bcall\s+(\w+)\s*\(", call_text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot parse call text: {call_text[:80]}")
    addfld_subroutine = match.group(1)
    open_idx = call_text.find("(", match.end() - 1)
    close_idx = call_text.rfind(")")
    if open_idx < 0 or close_idx < open_idx:
        raise ValueError(f"Cannot find call argument list: {call_text[:80]}")
    arg_text = call_text[open_idx + 1 : close_idx]
    args: Dict[str, str] = {}
    positional = 0
    for chunk in split_top_level(arg_text, ","):
        key, value = split_named_arg(chunk)
        if key is None:
            positional += 1
            key = f"arg{positional}"
        args[key] = value
    return addfld_subroutine, args


def update_pointer_targets(pointer_targets: Dict[str, str], clean_line: str) -> None:
    for statement in split_top_level(clean_line, ";"):
        match = re.search(r"\b([A-Za-z]\w*)\s*=>\s*(.+)$", statement)
        if match:
            pointer_targets[match.group(1).lower()] = compact_expr(match.group(2))


def maybe_start_block(clean_line: str) -> Optional[Tuple[str, str]]:
    if re.match(r"^\s*if\s*\(.*\)\s*then\b", clean_line, flags=re.IGNORECASE):
        return "if", compact_expr(clean_line)
    if re.match(r"^\s*do\b", clean_line, flags=re.IGNORECASE):
        return "do", compact_expr(clean_line)
    return None


def maybe_end_block(clean_line: str) -> Optional[str]:
    if re.match(r"^\s*(endif|end\s+if)\b", clean_line, flags=re.IGNORECASE):
        return "if"
    if re.match(r"^\s*(enddo|end\s+do)\b", clean_line, flags=re.IGNORECASE):
        return "do"
    return None


def pop_block(block_stack: List[Tuple[str, str]], block_type: str) -> None:
    for idx in range(len(block_stack) - 1, -1, -1):
        if block_stack[idx][0] == block_type:
            del block_stack[idx:]
            return


def rank_from_subroutine(addfld_subroutine: str) -> str:
    match = re.search(r"(\d+)d", addfld_subroutine, flags=re.IGNORECASE)
    return f"{match.group(1)}d" if match else ""


def first_pointer(args: Dict[str, str], pointer_snapshot: Dict[str, str]) -> Dict[str, str]:
    for key in sorted(args):
        if key.startswith("ptr_"):
            expr = compact_expr(args[key])
            target = pointer_snapshot.get(expr.lower(), "")
            if not target and "%" in expr:
                target = expr
            return {
                "pointer_arg": key,
                "pointer_kind": key[4:],
                "pointer_expr": expr,
                "pointer_target": target,
            }
    return {
        "pointer_arg": "",
        "pointer_kind": "",
        "pointer_expr": "",
        "pointer_target": "",
    }


def context_text(block_stack: Sequence[Tuple[str, str]], block_type: str) -> str:
    return " > ".join(text for kind, text in block_stack if kind == block_type)


def record_from_call(
    source_file: Path,
    start_line: int,
    end_line: int,
    call_text: str,
    pointer_snapshot: Dict[str, str],
    block_stack: Sequence[Tuple[str, str]],
    enclosing_subroutine: str,
) -> Dict[str, object]:
    addfld_subroutine, args = parse_call_text(call_text)
    fname_expr = compact_expr(args.get("fname"))
    literal_fname = parse_fortran_string(fname_expr)
    fname = literal_fname if literal_fname is not None else expr_to_template(fname_expr)
    pointer = first_pointer(args, pointer_snapshot)
    record: Dict[str, object] = {
        "source_file": str(source_file),
        "source_line": start_line,
        "end_line": end_line,
        "addfld_subroutine": addfld_subroutine,
        "rank": rank_from_subroutine(addfld_subroutine),
        "fname": fname,
        "fname_expr": fname_expr,
        "is_dynamic_fname": literal_fname is None,
        "units": expr_to_template(args.get("units")),
        "avgflag": expr_to_template(args.get("avgflag")),
        "type2d": expr_to_template(args.get("type2d")),
        "default": expr_to_template(args.get("default")),
        "long_name": expr_to_template(args.get("long_name")),
        "condition_context": context_text(block_stack, "if"),
        "loop_context": context_text(block_stack, "do"),
        "enclosing_subroutine": enclosing_subroutine,
    }
    record.update(pointer)
    return record


def extract_records(source_file: Path, call_regex: str = DEFAULT_CALL_REGEX) -> List[Dict[str, object]]:
    call_pattern = re.compile(rf"\bcall\s+({call_regex})\s*\(", flags=re.IGNORECASE)
    pointer_targets: Dict[str, str] = {}
    block_stack: List[Tuple[str, str]] = []
    records: List[Dict[str, object]] = []
    enclosing_subroutine = ""

    in_call = False
    call_lines: List[str] = []
    call_start_line = 0
    call_pointer_snapshot: Dict[str, str] = {}
    call_block_snapshot: List[Tuple[str, str]] = []
    call_subroutine = ""
    depth = 0

    lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, raw in enumerate(lines, start=1):
        clean = normalized_source_line(raw)
        if not clean:
            continue

        sub_match = re.match(r"^\s*subroutine\s+(\w+)\b", clean, flags=re.IGNORECASE)
        if sub_match:
            enclosing_subroutine = sub_match.group(1)
            pointer_targets = {}
            block_stack = []

        if re.match(r"^\s*end\s+subroutine\b", clean, flags=re.IGNORECASE):
            enclosing_subroutine = ""
            pointer_targets = {}
            block_stack = []
            continue

        if in_call:
            call_lines.append(clean)
            depth += paren_delta(clean)
            if depth <= 0:
                records.append(
                    record_from_call(
                        source_file=source_file,
                        start_line=call_start_line,
                        end_line=lineno,
                        call_text=" ".join(call_lines),
                        pointer_snapshot=call_pointer_snapshot,
                        block_stack=call_block_snapshot,
                        enclosing_subroutine=call_subroutine,
                    )
                )
                in_call = False
                call_lines = []
            continue

        ended = maybe_end_block(clean)
        if ended:
            pop_block(block_stack, ended)
            continue

        call_match = call_pattern.search(clean)
        if call_match:
            update_pointer_targets(pointer_targets, clean[: call_match.start()])
            call_start_line = lineno
            call_lines = [clean[call_match.start() :]]
            call_pointer_snapshot = dict(pointer_targets)
            call_block_snapshot = list(block_stack)
            call_subroutine = enclosing_subroutine
            depth = paren_delta(call_lines[0])
            if depth <= 0:
                records.append(
                    record_from_call(
                        source_file=source_file,
                        start_line=call_start_line,
                        end_line=lineno,
                        call_text=" ".join(call_lines),
                        pointer_snapshot=call_pointer_snapshot,
                        block_stack=call_block_snapshot,
                        enclosing_subroutine=call_subroutine,
                    )
                )
                call_lines = []
            else:
                in_call = True
            continue

        update_pointer_targets(pointer_targets, clean)
        started = maybe_start_block(clean)
        if started:
            block_stack.append(started)

    if in_call:
        raise ValueError(f"Unclosed hist_addfld call starting at line {call_start_line}")
    return records


CSV_FIELDS = [
    "source_file",
    "source_line",
    "end_line",
    "addfld_subroutine",
    "rank",
    "fname",
    "fname_expr",
    "is_dynamic_fname",
    "units",
    "avgflag",
    "type2d",
    "default",
    "long_name",
    "pointer_arg",
    "pointer_kind",
    "pointer_expr",
    "pointer_target",
    "condition_context",
    "loop_context",
    "enclosing_subroutine",
]


def build_summary(records: Sequence[Dict[str, object]], source_file: Path, call_regex: str) -> Dict[str, object]:
    literal_names = [
        str(record["fname"])
        for record in records
        if record.get("fname") and not record.get("is_dynamic_fname")
    ]
    duplicates = sorted(name for name, count in Counter(literal_names).items() if count > 1)
    return {
        "schema_version": "1.0",
        "source_file": str(source_file),
        "call_regex": call_regex,
        "record_count": len(records),
        "dynamic_fname_count": sum(1 for record in records if record.get("is_dynamic_fname")),
        "by_addfld_subroutine": dict(Counter(str(record["addfld_subroutine"]) for record in records)),
        "by_rank": dict(Counter(str(record["rank"]) for record in records)),
        "by_pointer_kind": dict(Counter(str(record["pointer_kind"]) for record in records)),
        "duplicate_literal_fnames": duplicates,
    }


def write_json(records: Sequence[Dict[str, object]], summary: Dict[str, object], out) -> None:
    json.dump({"summary": summary, "variables": list(records)}, out, indent=2)
    out.write("\n")


def write_csv(records: Sequence[Dict[str, object]], out) -> None:
    writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(record)


def markdown_escape(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ")


def write_markdown(records: Sequence[Dict[str, object]], summary: Dict[str, object], out) -> None:
    out.write("# EcoSIM Output Variables\n\n")
    out.write(f"- Source: `{summary['source_file']}`\n")
    out.write(f"- Records: {summary['record_count']}\n")
    out.write(f"- Dynamic `fname` expressions: {summary['dynamic_fname_count']}\n")
    if summary["duplicate_literal_fnames"]:
        out.write("- Duplicate literal names: " + ", ".join(f"`{x}`" for x in summary["duplicate_literal_fnames"]) + "\n")
    out.write("\n")
    fields = ["source_line", "addfld_subroutine", "rank", "fname", "units", "avgflag", "type2d", "pointer_kind", "long_name"]
    out.write("| " + " | ".join(fields) + " |\n")
    out.write("| " + " | ".join(["---"] * len(fields)) + " |\n")
    for record in records:
        out.write("| " + " | ".join(markdown_escape(record.get(field, "")) for field in fields) + " |\n")


def open_output(path: Optional[Path]):
    if path is None:
        return sys.stdout
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8", newline="")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract EcoSIM history output variables from Fortran hist_addfld registration calls."
    )
    parser.add_argument("source_file", type=Path, help="Fortran source file, such as HistDataType.F90.")
    parser.add_argument(
        "--format",
        choices=("json", "csv", "markdown"),
        default="markdown",
        help="Output format. JSON includes summary metadata and records.",
    )
    parser.add_argument("--output", type=Path, help="Output file path. Defaults to stdout.")
    parser.add_argument(
        "--call-regex",
        default=DEFAULT_CALL_REGEX,
        help="Case-insensitive regex for add-field subroutine names. Default: hist_addfld\\w*",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if not args.source_file.exists():
        print(f"ERROR: source file does not exist: {args.source_file}", file=sys.stderr)
        return 2
    try:
        records = extract_records(args.source_file, args.call_regex)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not records:
        print(
            f"ERROR: no calls matching {args.call_regex!r} found in {args.source_file}",
            file=sys.stderr,
        )
        return 1
    summary = build_summary(records, args.source_file, args.call_regex)
    with open_output(args.output) as out:
        if args.format == "json":
            write_json(records, summary, out)
        elif args.format == "csv":
            write_csv(records, out)
        else:
            write_markdown(records, summary, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
