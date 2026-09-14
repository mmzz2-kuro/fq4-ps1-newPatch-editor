#!/usr/bin/env python3
"""Document FQ4's weighted party-species graphics budget."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "work/fq4/001/original/SLPS_006.04"
OUT = ROOT / "docs/fq4/analysis/015"
LOAD = 0x80010000
HEADER = 0x800
TABLE_RAM = 0x800FA220
CHECK_RAM = 0x80072A04
OLD_LIMIT = 0x1E0
NEW_LIMIT_EXCLUSIVE = 0x361
SITES = [0x80017F58, 0x8001832C, 0x80020A70, 0x80064F2C,
         0x80065874, 0x80065F04, 0x8006B27C, 0x80072C28]


def off(addr: int) -> int:
    return addr - LOAD + HEADER


def main() -> None:
    data = EXE.read_bytes()
    table = []
    for species in range(150):
        a, b, c = data[off(TABLE_RAM) + species * 3: off(TABLE_RAM) + species * 3 + 3]
        table.append({"species": species, "factors": [a, b, c], "cost": a * b * c})
    checks = []
    for addr in SITES:
        word = struct.unpack_from("<I", data, off(addr))[0]
        if word & 0xFFFF != OLD_LIMIT:
            raise ValueError(f"unexpected immediate at {addr:#x}: {word:#x}")
        checks.append({"ram": hex(addr), "file_offset": hex(off(addr)), "word": f"{word:08x}"})
    result = {
        "executable_sha256": hashlib.sha256(data).hexdigest(),
        "validator": hex(CHECK_RAM),
        "algorithm": "sum product of the three graphics-cost bytes once per distinct species; proposed species is included when absent",
        "original_comparison": "total < 480 (0x1e0)",
        "observed_costs": {str(cost): sum(x["cost"] == cost for x in table) for cost in sorted({x["cost"] for x in table})},
        "ordinary_species_capacity": 9,
        "capacity_is_not_fixed_species_count": True,
        "adopted_comparison": "total < 865 (0x361), allowing 18 ordinary 48-unit species",
        "comparison_sites": checks,
        "species_cost_table": table,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "race-limit-code.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("validator", "original_comparison", "ordinary_species_capacity", "adopted_comparison")}, indent=2))


if __name__ == "__main__":
    main()
