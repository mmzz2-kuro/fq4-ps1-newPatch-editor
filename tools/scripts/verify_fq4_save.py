#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path
from fq4_memcard import MemoryCard, BLOCK_SIZE, CHECKSUM_OFFSET


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("original",type=Path); ap.add_argument("edited",type=Path)
    args=ap.parse_args(); a=args.original.read_bytes(); b=args.edited.read_bytes()
    ca,cb=MemoryCard(a),MemoryCard(b)
    diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    allowed=set()
    for sa,sb in zip(ca.slots,cb.slots):
        pd=[i for i,(x,y) in enumerate(zip(sa.payload,sb.payload)) if x!=y]
        for i in pd:
            block=sa.blocks[i//BLOCK_SIZE]; allowed.add(block*BLOCK_SIZE+i%BLOCK_SIZE)
        sb.validate()
    result={"valid":len(a)==len(b)==131072 and all(i in allowed for i in diffs),"difference_count":len(diffs),
            "difference_offsets":[hex(i) for i in diffs],"directory_unchanged":a[:0x800]==b[:0x800],
            "checksum_offset":hex(CHECKSUM_OFFSET)}
    print(json.dumps(result,indent=2)); raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__": main()
