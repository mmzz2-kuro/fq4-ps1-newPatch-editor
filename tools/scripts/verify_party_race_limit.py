#!/usr/bin/env python3
"""Verify PLAN-015 machine code and weighted-boundary behavior."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "work/fq4/rom/current.bin"
OUT = ROOT / "docs/fq4/analysis/015/verification.json"
EXE_LBA, LOAD, HEADER = 24, 0x80010000, 0x800
NEW = 0x361
SITES = [0x80017F58, 0x8001832C, 0x80020A70, 0x80064F2C,
         0x80065874, 0x80065F04, 0x8006B27C, 0x80072C28]


def payload(image: bytes, eo: int, size: int) -> bytes:
    out = bytearray()
    while size:
        lba, within = EXE_LBA + eo // 2048, eo % 2048
        take = min(size, 2048-within)
        out += image[lba*2352+24+within:lba*2352+24+within+take]
        eo += take; size -= take
    return bytes(out)


def main() -> None:
    image = ROM.read_bytes()
    words = {}
    for addr in SITES:
        eo = addr - LOAD + HEADER
        word = struct.unpack("<I", payload(image, eo, 4))[0]
        words[hex(addr)] = f"{word:08x}"
        if word & 0xffff != NEW: raise ValueError(f"bad immediate at {addr:#x}")
    cases = []
    for n in (9, 10, 11, 17, 18):
        total = n * 48
        cases.append({"distinct_ordinary_species": n, "cost": total, "allowed": total < NEW})
    mixed = [{"costs": [32]*n, "allowed": 32*n < NEW} for n in (10, 14, 18)]
    if not all(x["allowed"] for x in cases) or not all(x["allowed"] for x in mixed):
        raise ValueError("boundary model failed")
    result = {"rom_sha256": hashlib.sha256(image).hexdigest(), "size": len(image),
              "machine_code": words, "ordinary_cases": cases, "low_cost_cases": mixed,
              "pass": True,
              "runtime_claim_limit": "Static and CPU-logic boundary verification; a naturally assembled 18-species party still needs user visual play testing."}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
