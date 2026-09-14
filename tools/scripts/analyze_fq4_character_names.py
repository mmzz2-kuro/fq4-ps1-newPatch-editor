#!/usr/bin/env python3
"""Audit all FQ4 save records and name IDs without modifying source cards."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from fq4_memcard import CHARACTER_COUNT, SPECIES_COUNT, MemoryCard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cards", nargs="+", type=Path)
    parser.add_argument("--names", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    names = json.loads(args.names.read_text(encoding="utf-8"))
    report = {"cards": [], "target_matches": [], "name_id_usage": Counter()}
    for path in args.cards:
        card = MemoryCard.open(path)
        card_info = {"path": str(path), "slots": []}
        for slot_no, slot in enumerate(card.slots, 1):
            all_records = slot.characters(include_empty=True)
            visible = slot.characters()
            excluded = Counter()
            for c in all_records:
                if c.hp == 0: excluded["hp_zero"] += 1
                if c.class_id >= SPECIES_COUNT: excluded["class_out_of_range"] += 1
                if c.name_id >= CHARACTER_COUNT: excluded["name_out_of_range"] += 1
                if c.hp > 0 and c.class_id < SPECIES_COUNT and c.name_id < CHARACTER_COUNT:
                    report["name_id_usage"][c.name_id] += 1
                if c.level == 58 and c.hp == 608 and c.hr == 9 and c.at == 53 and c.ar == 57:
                    report["target_matches"].append({
                        "path": str(path), "slot": slot_no, "record": c.index,
                        "name_id": c.name_id, "mapped_name": names[c.name_id] if c.name_id < len(names) else None,
                        "class_id": c.class_id, "lv": c.level, "hp": c.hp, "hr": c.hr,
                        "at": c.at, "ar": c.ar, "df": c.df, "dr": c.dr,
                    })
            card_info["slots"].append({
                "slot": slot_no, "filename": slot.filename, "visible": len(visible),
                "all_records": len(all_records), "excluded_conditions": dict(excluded),
            })
        report["cards"].append(card_info)
    report["name_id_usage"] = {str(k): v for k, v in sorted(report["name_id_usage"].items())}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
