#!/usr/bin/env python3
"""Disassemble a RAM address range from an FQ4 PS-X EXE."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work/fq4/python-deps"))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("end", type=lambda value: int(value, 0))
    args = parser.parse_args()
    image = args.exe.read_bytes()
    load = struct.unpack_from("<I", image, 0x18)[0]
    file_start = args.start - load + 0x800
    file_end = args.end - load + 0x800
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    for instruction in md.disasm(image[file_start:file_end], args.start):
        print(f"{instruction.address:08x}: {instruction.bytes.hex():8} {instruction.mnemonic:8} {instruction.op_str}")


if __name__ == "__main__":
    main()
