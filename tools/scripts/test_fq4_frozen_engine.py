#!/usr/bin/env python3
"""Launch the frozen GUI's hidden engine mode with exact Windows arguments."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--bios", type=Path, required=True)
    parser.add_argument("--xdelta-exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expand-party-species-limit", action="store_true")
    args = parser.parse_args()
    command = [
        str(args.exe.resolve()), "--engine-json",
        "--original", str(args.original.resolve()),
        "--patch", str(args.patch.resolve()),
        "--bios", str(args.bios.resolve()),
        "--xdelta-exe", str(args.xdelta_exe.resolve()),
        "--output", str(args.output.resolve()),
    ]
    if args.expand_party_species_limit:
        command.append("--expand-party-species-limit")
    result = subprocess.run(command, cwd=tempfile.gettempdir(), timeout=90, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    print(f"exit_code={result.returncode}")
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
