#!/usr/bin/env python3
"""Map selected Korean menu strings to FQ4 codes and locate them in the disc."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "scripts"))
from survey_rom import Disc  # noqa: E402


ROM = ROOT / "work" / "fq4" / "rom" / "current.bin"
BIOS = ROOT / "korean-patch" / "SCPH1001.BIN"
OUTPUT_DIR = ROOT / "docs" / "fq4" / "analysis" / "004"
TARGETS = ("시간경과", "부대이동", "탐색")
FONT_BASE = 0x5F82C
GLYPH_SIZE = 30


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    return (lead << 8) | trail


def map_character(character: str, bios: bytes) -> dict[str, object]:
    euc = character.encode("euc_kr")
    if len(euc) != 2 or not all(byte >= 0xA1 for byte in euc):
        raise ValueError(f"not a KS X 1001 double-byte character: {character!r}")
    row, cell = euc[0] - 0x80, euc[1] - 0x80
    index = (row - 0x21) * 94 + (cell - 0x21)
    code = jis_to_sjis(row, cell)
    offset = FONT_BASE + index * GLYPH_SIZE
    glyph = bios[offset : offset + GLYPH_SIZE]
    if len(glyph) != GLYPH_SIZE:
        raise ValueError("glyph falls outside BIOS")
    return {
        "character": character,
        "euc_kr": euc.hex().upper(),
        "jis_row_cell": f"{row:02X}{cell:02X}",
        "game_code": f"{code:04X}",
        "font_index": index,
        "bios_offset": f"0x{offset:x}",
        "glyph_sha256": sha(glyph),
    }


def find_all(data: bytes, needle: bytes) -> list[int]:
    found: list[int] = []
    at = 0
    while True:
        at = data.find(needle, at)
        if at < 0:
            return found
        found.append(at)
        at += 1


def main() -> None:
    bios = BIOS.read_bytes()
    disc = Disc(ROM)
    unique: dict[str, dict[str, object]] = {}
    strings = []
    for text in TARGETS:
        mapped = [map_character(character, bios) for character in text]
        for item in mapped:
            unique.setdefault(str(item["character"]), item)
        encoded = bytes.fromhex("".join(str(item["game_code"]) for item in mapped))
        hits = []
        for record in disc.files:
            try:
                data = disc.read(record)
            except ValueError as error:
                if "non-Form1 sector" in str(error):
                    continue
                raise
            for offset in find_all(data, encoded):
                hits.append(
                    {
                        "iso_path": record["path"],
                        "file_offset": f"0x{offset:x}",
                        "raw_context": data[max(0, offset - 8) : offset + len(encoded) + 9].hex(),
                        "next_byte": f"0x{data[offset + len(encoded)]:02x}" if offset + len(encoded) < len(data) else None,
                    }
                )
        strings.append(
            {
                "text": text,
                "game_code_hex": encoded.hex().upper(),
                "tokens": [item["game_code"] for item in mapped],
                "hits": hits,
            }
        )
    result = {
        "source_rom": ROM.relative_to(ROOT).as_posix(),
        "source_rom_sha256": sha(ROM.read_bytes()),
        "mapping_basis": "KS X 1001 row/cell encoded into the corresponding Shift-JIS position; verified by prior 교/섭/중 samples",
        "font_base": f"0x{FONT_BASE:x}",
        "glyph_size": GLYPH_SIZE,
        "strings": strings,
        "unique_glyph_count": len(unique),
        "unique_glyphs": list(unique.values()),
    }
    if any(not entry["hits"] for entry in strings):
        missing = [entry["text"] for entry in strings if not entry["hits"]]
        raise SystemExit(f"target strings not found as contiguous code streams: {missing}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "menu-strings.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "menu-glyphs.json").write_text(
        json.dumps({"font_base": result["font_base"], "glyph_size": GLYPH_SIZE, "glyphs": result["unique_glyphs"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"strings": strings, "unique_glyph_count": len(unique)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
