#!/usr/bin/env python3
"""Extract the fixed-width spell names from the PS1 executable copies."""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START = 0xEC34C
WIDTH = 11
NAMED_COUNT = 44
MAX_SAVE_ID = 53


def decode_patched(raw: bytes, mapping: dict[int, str]) -> str:
    raw = raw.split(b"\0", 1)[0].rstrip(b" ")
    chars = []
    i = 0
    while i < len(raw):
        if i + 1 < len(raw):
            code = (raw[i] << 8) | raw[i + 1]
            if code == 0x8140:
                chars.append(" ")
                i += 2
                continue
            if code in mapping:
                chars.append(mapping[code])
                i += 2
                continue
        if raw[i] < 0x80:
            chars.append(chr(raw[i]))
            i += 1
        else:
            chars.append("?")
            i += 1
    return "".join(chars).strip()


def main() -> None:
    original = (ROOT / "work/fq4/001/original/SLPS_006.04").read_bytes()
    patched = (ROOT / "work/fq4/001/patched/SLPS_006.04").read_bytes()
    entries = json.loads((ROOT / "docs/fq4/analysis/005/encoding-map.json").read_text(encoding="utf-8"))["mapping"]
    mapping = {int(row["game_code"], 16): bytes.fromhex(row["euc_kr"]).decode("euc-kr")
               for row in entries if not row.get("blank")}
    names = []
    for spell_id in range(1, MAX_SAVE_ID + 1):
        if spell_id < NAMED_COUNT:
            off = START + spell_id * WIDTH
            jp = unicodedata.normalize("NFKC", original[off:off + WIDTH].split(b"\0", 1)[0].decode("cp932", "replace")).strip()
            ko = decode_patched(patched[off:off + WIDTH], mapping)
            if not ko or "?" in ko:
                ko = f"미확인 마법 {spell_id}"
            source = "patched-rom" if not ko.startswith("미확인") else "unknown"
        else:
            off = None
            jp = ""
            ko = f"미확인 마법 {spell_id}"
            source = "unknown"
        names.append({"id": spell_id, "name": ko, "original": jp, "source": source,
                      "offset": f"0x{off:X}" if off is not None else None})
    output = ROOT / "tools/FQ4SaveEditor/spell_names.json"
    output.write_text(json.dumps(names, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output, len(names))


if __name__ == "__main__":
    main()
