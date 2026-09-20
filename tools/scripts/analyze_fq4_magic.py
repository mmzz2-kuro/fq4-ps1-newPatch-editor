#!/usr/bin/env python3
"""Record class spell-list evidence from existing memory cards."""
from __future__ import annotations

import json
from pathlib import Path

from fq4_memcard import MemoryCard, MAGIC_OFFSET, MAGIC_END

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/fq4/analysis/038"


def main() -> None:
    slots = []
    for path in sorted((ROOT / "memcard").rglob("*")):
        if path.suffix.lower() not in (".mcd", ".srm"):
            continue
        try:
            card = MemoryCard.open(path)
        except Exception:
            continue
        for index, slot in enumerate(card.slots):
            rows = slot.magic_sets()
            end = MAGIC_OFFSET + sum(2 + len(row.spell_ids) for row in rows)
            slots.append({
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "slot": index,
                "entry_count": len(rows),
                "terminator_offset": f"0x{end:04X}",
                "class_6": list(slot.spells_for_class(6) or ()),
                "class_13": list(slot.spells_for_class(13) or ()),
                "max_spell_id": max((spell for row in rows for spell in row.spell_ids), default=0),
            })
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"magic_start": f"0x{MAGIC_OFFSET:04X}", "safe_end_exclusive": f"0x{MAGIC_END:04X}",
              "format": "class_id u8, count u8, spell_id[count], repeated, FF terminator, zero padding",
              "slots": slots}
    (OUT / "save-magic-table.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"analyzed {len(slots)} slots")


if __name__ == "__main__":
    main()
