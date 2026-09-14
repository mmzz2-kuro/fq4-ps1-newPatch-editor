#!/usr/bin/env python3
"""Exhaustively verify the dense FQ4 Hangul lookup arithmetic without changing a ROM."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "fq4" / "analysis" / "005" / "lookup-verification.json"
FONT_BASE = 0x801E0000
GLYPH_BYTES = 30


def jis_to_sjis(row: int, cell: int) -> int:
    lead = ((row - 0x21) // 2) + 0x81
    if lead > 0x9F:
        lead += 0x40
    if (row - 0x21) % 2 == 0:
        trail = cell + 0x1F
        if trail >= 0x7F:
            trail += 1
    else:
        trail = cell + 0x7E
    return lead << 8 | trail


def lookup(code: int) -> int | None:
    lead, trail = code >> 8, code & 0xFF
    if 0x81 <= lead <= 0x9F:
        lead_index = lead - 0x81
    elif 0xE0 <= lead <= 0xEF:
        lead_index = lead - 0xC1
    else:
        return None
    row = lead_index * 2 + 0x21
    if 0x40 <= trail <= 0x7E:
        cell = trail - 0x1F
    elif 0x80 <= trail <= 0x9E:
        cell = trail - 0x20
    elif 0x9F <= trail <= 0xFC:
        row += 1
        cell = trail - 0x7E
    else:
        return None
    if not (0x30 <= row <= 0x48 and 0x21 <= cell <= 0x7E):
        return None
    index = (row - 0x30) * 94 + (cell - 0x21)
    return FONT_BASE + index * GLYPH_BYTES


def main() -> None:
    failures = []
    tested = 0
    for row in range(0x30, 0x49):
        for cell in range(0x21, 0x7F):
            code = jis_to_sjis(row, cell)
            expected = FONT_BASE + tested * GLYPH_BYTES
            actual = lookup(code)
            if actual != expected:
                failures.append({"code": f"{code:04X}", "expected": hex(expected), "actual": None if actual is None else hex(actual)})
            tested += 1
    boundaries = [0x0000, 0x8140, jis_to_sjis(0x2F, 0x7E), jis_to_sjis(0x49, 0x21), 0x817F, 0x80A1, 0xF040, 0xFFFF]
    boundary_failures = [f"{code:04X}" for code in boundaries if lookup(code) is not None]
    result = {
        "status": "pass" if not failures and not boundary_failures and tested == 2350 else "fail",
        "tested_valid_codes": tested,
        "valid_failures": failures,
        "tested_invalid_boundaries": [f"{code:04X}" for code in boundaries],
        "invalid_boundary_failures": boundary_failures,
        "first_pointer": hex(lookup(jis_to_sjis(0x30, 0x21)) or 0),
        "last_pointer": hex(lookup(jis_to_sjis(0x48, 0x7E)) or 0),
        "end_exclusive": hex(FONT_BASE + 2350 * GLYPH_BYTES),
        "r3000a_implementation_requirements": [
            "preserve a0 until fallback is selected",
            "place a safe instruction or nop after each load",
            "use explicit branch and jump delay slots",
            "call BIOS B0(51h) for codes outside the dense Hangul domain or before font_ready",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
