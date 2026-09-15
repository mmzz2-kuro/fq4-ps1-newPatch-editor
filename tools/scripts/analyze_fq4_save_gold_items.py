#!/usr/bin/env python3
"""Survey FQ4 PS1 save payloads for gold and item-table candidates."""
from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

from fq4_memcard import (
    CHECKSUM_COUNT,
    CHECKSUM_OFFSET,
    CHARACTER_COUNT,
    CHARACTER_OFFSET,
    CHARACTER_STRIDE,
    MemoryCard,
    SaveFormatError,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "fq4" / "analysis" / "033"
CHARACTER_END = CHARACTER_OFFSET + CHARACTER_COUNT * CHARACTER_STRIDE
PROTECTED = set(range(CHARACTER_OFFSET, CHARACTER_END)) | set(range(CHECKSUM_OFFSET, CHECKSUM_OFFSET + CHECKSUM_COUNT))


def load_slots() -> list[dict[str, object]]:
    slots: list[dict[str, object]] = []
    for path in sorted((ROOT / "memcard").rglob("*")):
        if path.suffix.lower() not in {".mcd", ".srm"}:
            continue
        try:
            card = MemoryCard.open(path)
        except SaveFormatError:
            continue
        for index, slot in enumerate(card.slots):
            slots.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "slot_index": index,
                    "filename": slot.filename,
                    "payload": bytes(slot.payload),
                }
            )
    return slots


def le_values(payload: bytes, width: int, start: int = 4, end: int = CHECKSUM_OFFSET) -> dict[int, int]:
    values = {}
    for off in range(start, end - width + 1):
        if any((off + n) in PROTECTED for n in range(width)):
            continue
        if width == 1:
            value = payload[off]
        elif width == 2:
            value = struct.unpack_from("<H", payload, off)[0]
        else:
            value = struct.unpack_from("<I", payload, off)[0]
        values[off] = value
    return values


def small_numeric_candidates(slots: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    for width, max_value in ((1, 99), (2, 9999), (4, 99999999)):
        all_values = [le_values(slot["payload"], width) for slot in slots]
        common_offsets = set(all_values[0])
        for values in all_values[1:]:
            common_offsets &= set(values)
        for off in sorted(common_offsets):
            values = [values_by_offset[off] for values_by_offset in all_values]
            if not all(0 <= value <= max_value for value in values):
                continue
            nonzero = sum(value != 0 for value in values)
            distinct = len(set(values))
            if nonzero == 0:
                continue
            if distinct == 1 and values[0] not in {1000, 999, 99, 1}:
                continue
            result.append(
                {
                    "offset": f"0x{off:04X}",
                    "width": width,
                    "values": values,
                    "distinct": distinct,
                    "nonzero": nonzero,
                    "paths": [f"{slot['path']}#{slot['slot_index'] + 1}" for slot in slots],
                }
            )
    return result


def byte_runs(payload: bytes, start: int = 4, end: int = CHECKSUM_OFFSET) -> list[dict[str, object]]:
    runs = []
    off = start
    while off < end:
        if off in PROTECTED or payload[off] == 0:
            off += 1
            continue
        begin = off
        while off < end and off not in PROTECTED and payload[off] != 0:
            off += 1
        if off - begin >= 8:
            runs.append({"start": begin, "end": off, "length": off - begin})
    return runs


def repeated_pair_tables(slots: list[dict[str, object]]) -> list[dict[str, object]]:
    payload = slots[0]["payload"]
    tables = []
    for start in range(4, CHECKSUM_OFFSET - 16):
        if start in PROTECTED:
            continue
        best = 0
        pairs = []
        for n in range(0, 512):
            off = start + n * 2
            if off + 2 > CHECKSUM_OFFSET or off in PROTECTED or off + 1 in PROTECTED:
                break
            item_id = payload[off]
            qty = payload[off + 1]
            if item_id == 0 and qty == 0:
                if best >= 8:
                    break
                if n == 0:
                    break
            if item_id <= 0xEF and qty <= 99:
                pairs.append((item_id, qty))
                best += 1
            else:
                break
        if best >= 12:
            values = []
            for slot in slots[: min(6, len(slots))]:
                sample = []
                data = slot["payload"]
                for n in range(min(best, 16)):
                    off = start + n * 2
                    sample.append([data[off], data[off + 1]])
                values.append(sample)
            tables.append({"offset": f"0x{start:04X}", "entry_width": 2, "entries": best, "samples": values})
    compact = []
    last_end = -1
    for table in tables:
        start = int(table["offset"], 16)
        end = start + table["entries"] * 2
        if start < last_end:
            continue
        compact.append(table)
        last_end = end
    return compact[:80]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    slots = load_slots()
    if not slots:
        raise SystemExit("no FQ4 slots found")
    run_report = []
    for slot in slots:
        runs = byte_runs(slot["payload"])
        run_report.append(
            {
                "slot": f"{slot['path']}#{slot['slot_index'] + 1}",
                "runs": [{"start": f"0x{r['start']:04X}", "end": f"0x{r['end']:04X}", "length": r["length"]} for r in runs[:80]],
            }
        )
    result = {
        "slot_count": len(slots),
        "slots": [{"path": slot["path"], "slot_index": slot["slot_index"], "filename": slot["filename"]} for slot in slots],
        "character_region": {"start": f"0x{CHARACTER_OFFSET:04X}", "end": f"0x{CHARACTER_END:04X}"},
        "checksum_region": {"start": f"0x{CHECKSUM_OFFSET:04X}", "end": f"0x{CHECKSUM_OFFSET + CHECKSUM_COUNT:04X}"},
        "small_numeric_candidates": small_numeric_candidates(slots)[:300],
        "nonzero_runs": run_report,
        "pair_table_candidates": repeated_pair_tables(slots),
    }
    (OUT / "gold-item-candidate-survey.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slot_count": len(slots), "numeric_candidates": len(result["small_numeric_candidates"]), "pair_tables": len(result["pair_table_candidates"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
