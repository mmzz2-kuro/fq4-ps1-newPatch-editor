#!/usr/bin/env python3
"""Inventory FQ4 Korean glyph use and calculate full-font storage/RAM options."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "fq4" / "analysis" / "005"
ORIGINAL_EXE = ROOT / "work" / "fq4" / "001" / "original" / "SLPS_006.04"
PATCHED_EXE = ROOT / "work" / "fq4" / "001" / "reproduced" / "SLPS_006.04"
KOREAN_BIOS = ROOT / "korean-patch" / "SCPH1001.BIN"
NORMAL_BIOS = ROOT / "original" / "scph1001.bin"
FONT_TABLE_BASE = 0x5F82C
HANGUL_FIRST_INDEX = (0x30 - 0x21) * 94
HANGUL_COUNT = 25 * 94
HANGUL_BIOS_START = FONT_TABLE_BASE + HANGUL_FIRST_INDEX * 30
HANGUL_BYTES = HANGUL_COUNT * 30


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jis_to_sjis(row: int, cell: int) -> int:
    lead = ((row - 0x21) // 2) + 0x81
    if lead > 0x9F:
        lead += 0x40
    if (row - 0x21) % 2 == 0:
        trail = cell + 0x1F
        if trail >= 0x7F:
            trail += 1
    else:
        trail = cell + 0x7E
    return (lead << 8) | trail


def save(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    original = ORIGINAL_EXE.read_bytes()
    patched = PATCHED_EXE.read_bytes()
    korean_bios = KOREAN_BIOS.read_bytes()
    normal_bios = NORMAL_BIOS.read_bytes()
    if len(original) != len(patched):
        raise ValueError("executable sizes differ")

    by_code: dict[int, dict[str, object]] = {}
    encoding_rows = []
    for lead in range(0xB0, 0xC9):
        for trail in range(0xA1, 0xFF):
            euc = bytes((lead, trail))
            character = euc.decode("euc_kr")
            row, cell = lead - 0x80, trail - 0x80
            code = jis_to_sjis(row, cell)
            dense_index = (lead - 0xB0) * 94 + (trail - 0xA1)
            bios_offset = HANGUL_BIOS_START + dense_index * 30
            glyph = korean_bios[bios_offset : bios_offset + 30]
            item = {
                "character": character,
                "euc_kr": euc.hex().upper(),
                "jis_row_cell": f"{row:02X}{cell:02X}",
                "game_code": f"{code:04X}",
                "dense_index": dense_index,
                "bios_offset": f"0x{bios_offset:x}",
                "glyph_sha256": sha(glyph),
                "blank": not any(glyph),
            }
            by_code[code] = item
            encoding_rows.append(item)

    korean_region = korean_bios[HANGUL_BIOS_START : HANGUL_BIOS_START + HANGUL_BYTES]
    normal_region = normal_bios[HANGUL_BIOS_START : HANGUL_BIOS_START + HANGUL_BYTES]
    if korean_region == normal_region:
        raise ValueError("normal and Korean Hangul regions unexpectedly match")

    def valid_code(data: bytes, offset: int) -> int | None:
        if offset + 2 > len(data):
            return None
        code = int.from_bytes(data[offset : offset + 2], "big")
        return code if code in by_code else None

    raw_runs = []
    for parity in (0, 1):
        offset = parity
        while offset + 2 <= len(patched):
            if valid_code(patched, offset) is None:
                offset += 2
                continue
            start = offset
            codes = []
            while offset + 2 <= len(patched):
                code = valid_code(patched, offset)
                if code is None:
                    break
                codes.append(code)
                offset += 2
            if len(codes) >= 2:
                changed = sum(patched[start + i * 2 : start + i * 2 + 2] != original[start + i * 2 : start + i * 2 + 2] for i in range(len(codes)))
                if changed:
                    raw_runs.append({"start": start, "end": offset, "codes": codes, "changed_tokens": changed})
            if offset == start:
                offset += 2

    # Prefer the longest/highest-change alignment when two byte-shifted candidates overlap.
    chosen = []
    occupied: set[int] = set()
    for run in sorted(raw_runs, key=lambda item: (len(item["codes"]), item["changed_tokens"]), reverse=True):
        byte_range = set(range(run["start"], run["end"]))
        if occupied & byte_range:
            continue
        chosen.append(run)
        occupied |= byte_range
    chosen.sort(key=lambda item: item["start"])

    confirmed_counts: Counter[int] = Counter()
    occurrences: defaultdict[int, list[str]] = defaultdict(list)
    run_records = []
    for run in chosen:
        text = "".join(str(by_code[code]["character"]) for code in run["codes"])
        run_records.append({
            "file": "/SLPS_006.04;1",
            "offset": f"0x{run['start']:x}",
            "byte_length": run["end"] - run["start"],
            "token_count": len(run["codes"]),
            "changed_tokens": run["changed_tokens"],
            "text": text,
            "codes": [f"{code:04X}" for code in run["codes"]],
            "classification": "confirmed_lower_bound: changed run of at least two mapped Hangul codes",
        })
        for index, code in enumerate(run["codes"]):
            confirmed_counts[code] += 1
            if len(occurrences[code]) < 8:
                occurrences[code].append(f"0x{run['start'] + index * 2:x}")

    single_counts: Counter[int] = Counter()
    single_samples: defaultdict[int, list[str]] = defaultdict(list)
    for offset in range(len(patched) - 1):
        code = valid_code(patched, offset)
        if code is None or offset in occupied or offset + 1 in occupied:
            continue
        if patched[offset : offset + 2] == original[offset : offset + 2]:
            continue
        single_counts[code] += 1
        if len(single_samples[code]) < 8:
            single_samples[code].append(f"0x{offset:x}")

    confirmed = []
    for code in sorted(confirmed_counts):
        row = dict(by_code[code])
        row.update({"occurrences": confirmed_counts[code], "sample_offsets": occurrences[code]})
        confirmed.append(row)
    candidates = []
    for code in sorted(single_counts):
        row = dict(by_code[code])
        row.update({"candidate_occurrences": single_counts[code], "sample_offsets": single_samples[code], "reason": "changed isolated mapped code; text context not yet proven"})
        candidates.append(row)

    full_sector_count = math.ceil(HANGUL_BYTES / 2048)
    direct_map_bytes = HANGUL_COUNT * 2
    used_bytes = len(confirmed) * 30
    used_plus_candidates = len({int(row["game_code"], 16) for row in confirmed + candidates}) * 30
    storage = {
        "dummy_file": {
            "iso_path": "/DUMMY.DUM;1",
            "lba": 24184,
            "size": 38230976,
            "form": "Mode 2 Form 1",
            "executable_filename_references": 0,
            "proposal": f"replace first {full_sector_count} payload sectors with a font header and dense Hangul data; retain ISO extent and disc size",
            "validation_required": "runtime proof that DUMMY.DUM content is never consumed for gameplay or seek timing",
        },
        "used_only": {
            "confirmed_lower_bound_glyphs": len(confirmed),
            "confirmed_glyph_bytes": used_bytes,
            "confirmed_plus_candidates_glyph_bytes": used_plus_candidates,
            "direct_dense_map_bytes": direct_map_bytes,
            "note": "smaller, but incomplete until isolated candidates and other text containers are resolved",
        },
        "full_dense_hangul": {
            "glyphs": HANGUL_COUNT,
            "glyph_bytes": HANGUL_BYTES,
            "sector_count": full_sector_count,
            "sector_payload_bytes": full_sector_count * 2048,
            "padding_bytes": full_sector_count * 2048 - HANGUL_BYTES,
            "lookup_metadata_bytes": 0,
            "note": "code can calculate a dense index; avoids static text omissions",
        },
        "recommendation": "full_dense_hangul",
        "reason": "70,500 bytes fit in 35 existing DUMMY.DUM sectors and remove correctness dependence on a heuristic text inventory",
    }

    t_addr = struct.unpack_from("<I", patched, 0x18)[0]
    t_size = struct.unpack_from("<I", patched, 0x1C)[0]
    stack = struct.unpack_from("<I", patched, 0x30)[0]
    stack_reserve_addr = 0x80114D18
    stack_reserve_off = stack_reserve_addr - t_addr + 0x800
    stack_reserve = struct.unpack_from("<I", patched, stack_reserve_off)[0]
    heap_start = 0x80182068
    heap_size = stack - stack_reserve - heap_start
    font_reserve = math.ceil(HANGUL_BYTES / 1024) * 1024
    ram = {
        "executable": {"load_address": hex(t_addr), "text_size": t_size, "loaded_end": hex(t_addr + t_size)},
        "stack": {"initial_pointer": hex(stack), "startup_reserve": stack_reserve},
        "bios_heap": {
            "initheap_wrapper": "0x80082cec (A0:39h)",
            "start": hex(heap_start),
            "size": heap_size,
            "end": hex(heap_start + heap_size),
            "main_allocation_wrapper": "0x80082d9c (A0:33h malloc)",
            "main_allocation_call": "0x80013a10",
            "request_strategy": "starts at 0x200000 and subtracts 0x400 until malloc succeeds; result and size become the game memory pool",
        },
        "proposal": {
            "reserve_bytes": font_reserve,
            "font_bytes": HANGUL_BYTES,
            "alignment_padding": font_reserve - HANGUL_BYTES,
            "remaining_game_pool_estimate": heap_size - font_reserve,
            "method": "reserve the top of the successfully allocated game pool before its custom allocator is initialized; store a persistent font pointer",
            "load": "read 35 sectors from DUMMY.DUM into the reserved block after CD initialization, then set font_ready",
        },
        "risks": [
            "Reducing the game pool by 70,656 bytes requires long-play and scene-transition regression tests.",
            "Exact CD file/read wrappers and synchronization point must be traced before implementation.",
            "The 0x80116000..0x80182068 gap contains referenced buffers and is not a safe extension area.",
        ],
    }

    lookup = {
        "recommended": "dense arithmetic",
        "accepted_code_domain": "Shift-JIS positions corresponding to JIS rows 0x30..0x48 and cells 0x21..0x7E",
        "algorithm": [
            "convert Shift-JIS lead/trail to JIS row/cell",
            "reject rows outside 0x30..0x48 or cells outside 0x21..0x7E",
            "index = (row - 0x30) * 94 + (cell - 0x21)",
            "return font_base + index * 30 when font_ready",
            "otherwise preserve a0 and dispatch to BIOS B0(51h)",
        ],
        "data_table_bytes": 0,
        "worst_case": "constant time",
        "abi": {"input": "a0=game code", "output": "v0=30-byte glyph pointer", "fallback": "t1=0x51, t2=0xB0, a0 unchanged"},
        "r3000a_rules": ["protect every load result with an independent instruction or nop", "verify branch and jump delay slots", "avoid unaligned halfword loads"],
        "implementation_gate": "assemble and test the loader plus lookup in PLAN-006; no ROM write in PLAN-005",
    }

    save("encoding-map.json", {
        "mapping_count": len(encoding_rows),
        "bios_region": {"start": hex(HANGUL_BIOS_START), "end_exclusive": hex(HANGUL_BIOS_START + HANGUL_BYTES), "bytes": HANGUL_BYTES, "normal_sha256": sha(normal_region), "korean_sha256": sha(korean_region)},
        "blank_glyphs": sum(bool(row["blank"]) for row in encoding_rows),
        "mapping": encoding_rows,
    })
    save("text-candidates.json", {"method": "changed executable bytes; maximal aligned runs of two or more mapped codes", "confirmed_runs": run_records, "isolated_candidate_code_count": len(candidates), "limitations": ["Single-character strings remain candidates.", "Compressed, graphical and XA text are outside this extractor.", "Static byte grammar can still admit binary false positives."]})
    save("used-glyphs.json", {"status": "confirmed lower bound plus isolated candidates", "confirmed_unique": len(confirmed), "confirmed_occurrences": sum(confirmed_counts.values()), "isolated_candidate_unique": len(candidates), "isolated_candidate_occurrences": sum(single_counts.values()), "confirmed": confirmed, "candidates": candidates})
    save("storage-options.json", storage)
    save("ram-loader-options.json", ram)
    save("lookup-design.json", lookup)
    print(json.dumps({"mapping": len(encoding_rows), "confirmed_runs": len(run_records), "confirmed_unique": len(confirmed), "isolated_candidate_unique": len(candidates), "full_font_bytes": HANGUL_BYTES, "font_sectors": full_sector_count, "heap_size": heap_size, "font_reserve": font_reserve, "remaining_pool": heap_size - font_reserve, "recommendation": storage["recommendation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
