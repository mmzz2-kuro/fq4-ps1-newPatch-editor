#!/usr/bin/env python3
"""Inspect raw FQ4 PS1 memory-card images without modifying them."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from fq4_memcard import MemoryCard


def inspect(path: Path) -> None:
    raw = path.read_bytes()
    card = MemoryCard(raw)
    print(f"file={path}")
    print(f"size={len(raw)} sha256={hashlib.sha256(raw).hexdigest()}")
    print(f"header={raw[:16].hex()} raw_ps1_header={raw[:2] == b'MC'}")
    print(f"directory_checksums={sum(e.checksum_ok for e in card.entries)}/{len(card.entries)}")
    print(f"fq4_slots={len(card.slots)} exact_round_trip={card.render() == raw}")
    for index, slot in enumerate(card.slots, 1):
        chars = slot.characters()
        print(
            f"slot[{index}]={slot.filename} start={slot.start_block} "
            f"blocks={','.join(map(str, slot.blocks))} characters={len(chars)} "
            f"checksums={slot.payload[0x7da6:0x7dae].hex()}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for number, path in enumerate(args.paths):
        if number:
            print()
        inspect(path)


if __name__ == "__main__":
    main()
