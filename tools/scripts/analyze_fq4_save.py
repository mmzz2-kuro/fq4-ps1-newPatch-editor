#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from fq4_memcard import MemoryCard, CHARACTER_OFFSET, CHARACTER_STRIDE, CHECKSUM_OFFSET


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze First Queen IV saves in a raw PS1 memory card")
    ap.add_argument("mcd", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    raw = args.mcd.read_bytes(); card = MemoryCard(raw)
    result = {
        "input": str(args.mcd), "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "slots": [{
            "filename": s.filename, "start_block": s.start_block, "blocks": s.blocks,
            "payload_checksum_bytes": s.payload[CHECKSUM_OFFSET:CHECKSUM_OFFSET+8].hex(),
            "editable_characters": [c.__dict__ for c in s.characters()],
        } for s in card.slots],
        "layout": {"character_offset": hex(CHARACTER_OFFSET), "stride": CHARACTER_STRIDE,
                   "checksum_offset": hex(CHECKSUM_OFFSET)},
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding="utf-8")
    else: print(text, end="")


if __name__ == "__main__": main()
