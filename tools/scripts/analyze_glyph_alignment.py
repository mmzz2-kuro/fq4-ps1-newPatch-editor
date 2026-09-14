#!/usr/bin/env python3
"""Derive the full-font base from PLAN-004 glyphs known to render correctly."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/fq4/analysis/004/poc-build.json"
OUT = ROOT / "docs/fq4/analysis/010/reference-glyphs.json"
BIOS = ROOT / "korean-patch/SCPH1001.BIN"
OLD_BASE = 0x69D60
STRIDE = 30


def dense_index(code: int) -> int:
    lead, trail = code >> 8, code & 0xFF
    lead_index = lead - 0x81 if lead < 0xA0 else lead - 0xC1
    row = lead_index * 2 + 0x21
    if trail < 0x7F:
        cell = trail - 0x1F
    elif trail < 0x9F:
        cell = trail - 0x20
    else:
        row += 1
        cell = trail - 0x7E
    if not (0x30 <= row <= 0x48 and 0x21 <= cell <= 0x7E):
        raise ValueError(f"outside Hangul domain: {code:04X}")
    return (row - 0x30) * 94 + (cell - 0x21)


def main() -> None:
    bios = BIOS.read_bytes()
    known = json.loads(SOURCE.read_text(encoding="utf-8"))["glyphs"]
    records = []
    bases = set()
    for item in known:
        code = int(item["code"], 16)
        index = dense_index(code)
        expected = int(item["source_bios_offset"], 16)
        derived_base = expected - index * STRIDE
        bases.add(derived_base)
        old = OLD_BASE + index * STRIDE
        records.append({
            "character": item["character"], "game_code": item["code"],
            "dense_index": index, "expected_bios_offset": hex(expected),
            "old_bios_offset": hex(old), "byte_error": old - expected,
            "derived_base": hex(derived_base),
            "expected_sha256": hashlib.sha256(bios[expected:expected+STRIDE]).hexdigest(),
            "old_sha256": hashlib.sha256(bios[old:old+STRIDE]).hexdigest(),
        })
    if bases != {0x69D68}:
        raise ValueError(f"known glyphs do not agree on one base: {sorted(map(hex, bases))}")
    result = {
        "status": "pass_root_cause_confirmed", "known_glyphs": len(records),
        "old_base": hex(OLD_BASE), "corrected_base": "0x69d68",
        "constant_byte_error": -8, "stride": STRIDE, "records": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
