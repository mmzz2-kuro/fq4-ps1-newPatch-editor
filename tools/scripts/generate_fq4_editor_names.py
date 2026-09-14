#!/usr/bin/env python3
"""Generate complete PS1 character/class labels from the original executable."""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "original" / "First Queen IV - Varcia Senki (Japan).bin"
UI = ROOT / "tools" / "FQ4SaveEditor"
EXE_LBA = 24
EXE_SIZE = 1_075_200
CHARACTER_TABLE = 0xE86B0
CHARACTER_COUNT = 640
CHARACTER_WIDTH = 10
CLASS_TABLE = 0xEA064
CLASS_COUNT = 220
CLASS_WIDTH = 9


def executable() -> bytes:
    raw = DISC.read_bytes()
    return b"".join(raw[(EXE_LBA + i) * 2352 + 24:(EXE_LBA + i) * 2352 + 2072]
                    for i in range((EXE_SIZE + 2047) // 2048))[:EXE_SIZE]


def decode_table(exe: bytes, start: int, count: int, width: int, prefix: str) -> list[str]:
    result = []
    for index in range(count):
        raw = exe[start + index * width:start + (index + 1) * width].split(b"\0", 1)[0].rstrip(b" ")
        text = unicodedata.normalize("NFKC", raw.decode("cp932", "replace")).strip()
        result.append(text or f"{prefix} ID {index}")
    return result


def main() -> None:
    exe = executable()
    characters = decode_table(exe, CHARACTER_TABLE, CHARACTER_COUNT, CHARACTER_WIDTH, "Name")
    classes = decode_table(exe, CLASS_TABLE, CLASS_COUNT, CLASS_WIDTH, "CLASS")
    # The Korean-patched game screen supplied by the user confirms this localized name.
    characters[265] = "트리스렌 / トリスラム"
    (UI / "character_names.json").write_text(json.dumps(characters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (UI / "class_names.json").write_text(json.dumps(classes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(characters)} character names and {len(classes)} class names")


if __name__ == "__main__":
    main()
