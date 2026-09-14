#!/usr/bin/env python3
"""Regression test for the supplied RetroArch raw PS1 memory card."""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

from fq4_memcard import MemoryCard

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "memcard" / "retroarch" / "fq4-kor-250826.srm"
OUTPUT = ROOT / "work" / "fq4" / "save-editor" / "current-retroarch-test.srm"


def main() -> None:
    raw = SOURCE.read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    card = MemoryCard(raw)
    assert len(card.slots) == 2
    assert card.render() == raw

    character = card.slots[0].characters()[0]
    new_hr = character.hr - 1 if character.hr > 1 else character.hr + 1
    card.slots[0].update_character(replace(character, hr=new_hr))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    card.save_as(OUTPUT)

    reread = MemoryCard.open(OUTPUT)
    edited = next(c for c in reread.slots[0].characters() if c.index == character.index)
    assert edited.hr == new_hr
    assert OUTPUT.suffix == ".srm"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
    print("PASS: RetroArch SRM parse, exact round trip, bounded edit, checksum, extension, source preservation")


if __name__ == "__main__":
    main()
