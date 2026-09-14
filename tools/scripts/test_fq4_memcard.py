#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile

from fq4_memcard import MemoryCard, SaveFormatError, CHARACTER_OFFSET, CHARACTER_STRIDE, CHECKSUM_OFFSET, BLOCK_SIZE

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'memcard'/'First Queen IV - Varcia Senki (Japan)_1.mcd'

def main():
    raw=SOURCE.read_bytes(); card=MemoryCard(raw)
    assert card.render()==raw
    slot=card.slots[0]; original=next(c for c in slot.characters() if c.index==229)
    slot.update_character(replace(original,class_id=10))
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'edited.mcd'; card.save_as(out); changed=out.read_bytes(); check=MemoryCard(changed)
        assert next(c for c in check.slots[0].characters() if c.index==229).class_id==10
        diffs=[i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b]
        species_payload=CHARACTER_OFFSET+229*CHARACTER_STRIDE+12
        expected={slot.blocks[species_payload//BLOCK_SIZE]*BLOCK_SIZE+species_payload%BLOCK_SIZE}
        for pos in range(CHECKSUM_OFFSET,CHECKSUM_OFFSET+8):
            physical=slot.blocks[pos//BLOCK_SIZE]*BLOCK_SIZE+pos%BLOCK_SIZE
            if raw[physical]!=changed[physical]: expected.add(physical)
        assert set(diffs)==expected,(diffs,sorted(expected))
    corrupt=bytearray(raw); corrupt[slot.blocks[0]*BLOCK_SIZE+0x100]^=1
    try: MemoryCard(corrupt)
    except SaveFormatError: pass
    else: raise AssertionError('corrupted payload checksum accepted')
    # Cross-check the twelve visible rows in the user-supplied slot-2 roster screenshot.
    expected = {
        220:(12,915,11,42,44,40,42), 222:(48,392,11,40,49,55,46),
        245:(83,696,9,64,59,62,65), 230:(52,470,8,11,67,61,66),
        248:(31,405,11,40,41,40,40), 229:(55,496,12,48,56,47,58),
        236:(41,390,8,36,38,50,55), 411:(50,999,11,62,99,64,99),
        410:(44,999,8,53,62,57,55), 417:(34,364,8,38,43,37,38),
        418:(24,301,9,36,39,34,36), 419:(28,324,9,38,42,34,38),
    }
    chars={c.index:c for c in MemoryCard(raw).slots[1].characters()}
    for index, values in expected.items():
        c=chars[index]
        assert (c.level,c.hp,c.hr,c.at,c.ar,c.df,c.dr)==values
    print('PASS: exact round trip, bounded edit, checksum rejection, slot-2 screen match')

if __name__=='__main__': main()


