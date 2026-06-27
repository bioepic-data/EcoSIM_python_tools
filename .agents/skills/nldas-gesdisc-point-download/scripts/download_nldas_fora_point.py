#!/usr/bin/env python3
"""Compatibility entry point for the NLDAS File A point downloader."""

from __future__ import annotations

from pathlib import Path
import runpy


SCRIPT = Path(__file__).with_name("download_nldas_forb_point.py")


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
