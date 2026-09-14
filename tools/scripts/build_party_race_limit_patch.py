#!/usr/bin/env python3
"""Apply FQ4's optional weighted party-species budget expansion."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/scripts"))
from build_bios_independent_poc import EXE_LBA, EXE_SIZE, LOAD, EXE_HEADER, fix_form1  # noqa: E402

DEFAULT_ROM = ROOT / "work/fq4/rom/current.bin"
OLD_EXCLUSIVE_BUDGET = 0x1E0
NEW_EXCLUSIVE_BUDGET = 0x361
SITES = (
    0x80017F58, 0x8001832C, 0x80020A70, 0x80064F2C,
    0x80065874, 0x80065F04, 0x8006B27C, 0x80072C28,
)


def sha256_bytes(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_species_budget_expansion(image: bytearray) -> dict[str, object]:
    """Patch one in-memory raw MODE2/2352 image and repair touched sectors."""
    if len(image) % 2352:
        raise ValueError("ROM 크기가 2352-byte sector 단위가 아닙니다.")
    baseline_sha = sha256_bytes(image)
    sector_count = (EXE_SIZE + 2047) // 2048
    exe = bytearray().join(
        image[(EXE_LBA + index) * 2352 + 24:(EXE_LBA + index) * 2352 + 2072]
        for index in range(sector_count)
    )[:EXE_SIZE]
    writes: list[dict[str, str]] = []
    touched: set[int] = set()
    for address in SITES:
        exe_offset = address - LOAD + EXE_HEADER
        old_word = struct.unpack_from("<I", exe, exe_offset)[0]
        if old_word & 0xFFFF != OLD_EXCLUSIVE_BUDGET or old_word >> 26 not in (10, 11):
            state = "이미 확장됨" if old_word & 0xFFFF == NEW_EXCLUSIVE_BUDGET else "예상하지 않은 값"
            raise ValueError(f"종족 제한 비교 명령 {address:#x}: {state} ({old_word:#010x})")
        new_word = (old_word & 0xFFFF0000) | NEW_EXCLUSIVE_BUDGET
        struct.pack_into("<I", exe, exe_offset, new_word)
        writes.append({
            "ram": hex(address), "file_offset": hex(exe_offset),
            "before": f"{old_word:08x}", "after": f"{new_word:08x}",
        })
        for position in range(exe_offset, exe_offset + 4):
            lba = EXE_LBA + position // 2048
            image[lba * 2352 + 24 + position % 2048] = exe[position]
            touched.add(lba)
    for lba in sorted(touched):
        position = lba * 2352
        sector = bytearray(image[position:position + 2352])
        fix_form1(sector)
        image[position:position + 2352] = sector
    return {
        "baseline_sha256": baseline_sha,
        "output_sha256": sha256_bytes(image),
        "size": len(image),
        "old_exclusive_budget": OLD_EXCLUSIVE_BUDGET,
        "new_exclusive_budget": NEW_EXCLUSIVE_BUDGET,
        "writes": writes,
        "touched_sectors": sorted(touched),
    }


def patch_file(source: Path, output: Path, overwrite: bool = False) -> dict[str, object]:
    """Patch a file transactionally. Source and output may be the same path."""
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"입력 BIN을 찾을 수 없습니다: {source}")
    if output.exists() and output != source and not overwrite:
        raise FileExistsError(f"출력 BIN이 이미 있습니다: {output}")
    image = bytearray(source.read_bytes())
    report = apply_species_budget_expansion(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.name}.species-budget.tmp")
    try:
        temp.write_bytes(image)
        os.replace(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=DEFAULT_ROM)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    output = args.output or args.input
    report = patch_file(args.input, output, args.overwrite)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
