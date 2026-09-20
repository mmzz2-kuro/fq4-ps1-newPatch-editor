#!/usr/bin/env python3
"""Check learned-magic editing against untouched sample cards."""
from __future__ import annotations

from pathlib import Path
from fq4_memcard import MemoryCard, SaveFormatError, MAGIC_OFFSET, MAGIC_END, CHECKSUM_OFFSET

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = [
    ROOT / "memcard/First Queen IV - Varcia Senki (Japan)_1.mcd",
    ROOT / "memcard/First Queen IV - Varcia Senki (Japan)_1-edited.mcd",
    ROOT / "memcard/retroarch/fq4-kor-250826.srm",
]


def main() -> None:
    checked = 0
    for path in SAMPLES:
        card = MemoryCard.open(path)
        for slot in card.slots:
            rows = slot.magic_sets()
            assert len(rows) == 43
            assert slot.spells_for_class(6) is not None
            assert slot.spells_for_class(13) is not None
            checked += 1

    card = MemoryCard.open(SAMPLES[0])
    slot = card.slots[2]
    before = bytes(slot.payload)
    old = slot.spells_for_class(6)
    assert old is not None
    new = [6, 7] if old != (6, 7) else [6, 7, 8]
    slot.set_class_spells(6, new)
    assert slot.spells_for_class(6) == tuple(new)
    slot.validate()
    after = bytes(slot.payload)
    changed = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
    assert all(MAGIC_OFFSET <= i < MAGIC_END or CHECKSUM_OFFSET <= i < CHECKSUM_OFFSET + 8
               for i in changed)
    assert card.render() != SAMPLES[0].read_bytes()
    reopened = MemoryCard(card.render())
    assert reopened.slots[2].spells_for_class(6) == tuple(new)
    assert reopened.slots[2].spells_for_class(13) == slot.spells_for_class(13)
    try:
        slot.set_class_spells(6, [6, 6])
    except SaveFormatError:
        pass
    else:
        raise AssertionError("duplicate spells were accepted")
    try:
        slot.set_class_spells(2, [6])
    except SaveFormatError:
        pass
    else:
        raise AssertionError("non-magic class was editable")

    slot.set_class_spells(6, list(old))
    assert bytes(slot.payload) == before
    assert card.render() == SAMPLES[0].read_bytes()
    print(f"{checked} slots parsed; mutation, checksum, isolation and exact restore passed")


if __name__ == "__main__":
    main()
