#!/usr/bin/env python3
"""Verify the full-font FQ4 artifact and execute loader/lookup paths in Unicorn."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "fq4" / "python-deps"))
sys.path.insert(0, str(ROOT / "tools" / "scripts"))
from unicorn import Uc, UC_ARCH_MIPS, UC_HOOK_CODE, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32  # noqa: E402
from unicorn.mips_const import *  # noqa: F403,E402
from survey_rom import Disc  # noqa: E402
from build_bios_independent_poc import fix_form1  # noqa: E402
from build_full_font_runtime import (  # noqa: E402
    BIOS, CODE_START, DUMMY_LBA, FONT_BIOS_OFF, FONT_BYTES, FONT_RESERVE, FONT_SECTORS,
    GAME_CD_DATA_SYNC, GAME_CD_READ, GLOBALS, LOOKUP, MAGIC, ORIGINAL_POOL_INIT, ROM,
)

OUT = ROOT / "docs" / "fq4" / "analysis" / "010" / "lookup-verification.json"
MANIFEST = ROOT / "docs" / "fq4" / "analysis" / "010" / "build-manifest.json"
SENTINEL = 0x80170000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jis_to_sjis(row: int, cell: int) -> int:
    lead = ((row - 0x21) // 2) + 0x81
    if lead > 0x9F: lead += 0x40
    if (row - 0x21) % 2 == 0:
        trail = cell + 0x1F
        if trail >= 0x7F: trail += 1
    else: trail = cell + 0x7E
    return lead << 8 | trail


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    image = ROM.read_bytes()
    if sha(image) != manifest["output_sha256"]:
        raise ValueError("artifact hash mismatch")
    for item in manifest["touched_sectors"]:
        lba = item["lba"]; sec = bytearray(image[lba * 2352:(lba + 1) * 2352]); check = bytearray(sec); fix_form1(check)
        if check != sec: raise ValueError(f"EDC/ECC mismatch at {lba}")
    disc = Disc(ROM)
    dummy = next(x for x in disc.files if x["path"] == "/DUMMY.DUM;1")
    if dummy["extents"][0]["lba"] != DUMMY_LBA or dummy["size"] != 38230976:
        raise ValueError("DUMMY extent changed")
    payload = b"".join(image[(DUMMY_LBA+i)*2352+24:(DUMMY_LBA+i)*2352+2072] for i in range(FONT_SECTORS))
    font = BIOS.read_bytes()[FONT_BIOS_OFF:FONT_BIOS_OFF + FONT_BYTES]
    if payload[:FONT_BYTES] != font or payload[FONT_BYTES:FONT_BYTES+4] != MAGIC:
        raise ValueError("disc font payload mismatch")

    exe_rec = next(x for x in disc.files if x["path"] == "/SLPS_006.04;1")
    exe = disc.read(exe_rec)
    uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(0, 0x200000)
    uc.mem_write(0x10000, exe[0x800:])
    initial_size = 0x75C00; pool = 0x80182068
    uc.mem_write(0x1159FC, initial_size.to_bytes(4, "little"))
    uc.mem_write(0x115C10, pool.to_bytes(4, "little"))
    calls = []

    def hook(mu: Uc, address: int, size: int, user: object) -> None:
        if address not in (ORIGINAL_POOL_INIT, GAME_CD_READ, GAME_CD_DATA_SYNC, 0xB0): return
        a0 = mu.reg_read(UC_MIPS_REG_A0) & 0xFFFFFFFF
        a1 = mu.reg_read(UC_MIPS_REG_A1) & 0xFFFFFFFF
        a2 = mu.reg_read(UC_MIPS_REG_A2) & 0xFFFFFFFF
        calls.append({"address": hex(address), "a0": hex(a0), "a1": hex(a1), "a2": hex(a2)})
        if address == GAME_CD_READ:
            index = a1 - DUMMY_LBA
            if a0 != 1 or not 0 <= index < 35: raise ValueError(f"wrong game CD wrapper arguments: a0={a0:x} a1={a1:x} a2={a2:x}")
            mu.mem_write(a2 & 0x1FFFFFFF, payload[index*2048:(index+1)*2048])
            mu.reg_write(UC_MIPS_REG_V0, 1)
        elif address == GAME_CD_DATA_SYNC:
            if a0 != 0 or a1 != 0: raise ValueError("wrong data sync arguments")
            mu.reg_write(UC_MIPS_REG_V0, 0)
        elif address == 0xB0:
            mu.emu_stop(); return
        ra = mu.reg_read(UC_MIPS_REG_RA)
        mu.reg_write(UC_MIPS_REG_PC, ra)

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.reg_write(UC_MIPS_REG_SP, 0x801FF000)
    uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
    uc.emu_start(CODE_START, SENTINEL, count=2000)
    reduced = int.from_bytes(uc.mem_read(0x1159FC, 4), "little")
    base = int.from_bytes(uc.mem_read(GLOBALS & 0x1FFFFFFF, 4), "little")
    ready = int.from_bytes(uc.mem_read((GLOBALS + 4) & 0x1FFFFFFF, 4), "little")
    if reduced != initial_size - FONT_RESERVE or base != pool + reduced or ready != 1:
        raise ValueError("loader state mismatch")

    tested = 0
    for row in range(0x30, 0x49):
        for cell in range(0x21, 0x7F):
            uc.reg_write(UC_MIPS_REG_A0, jis_to_sjis(row, cell)); uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
            uc.emu_start(LOOKUP, SENTINEL, count=500)
            got = uc.reg_read(UC_MIPS_REG_V0) & 0xFFFFFFFF
            if got != base + tested * 30: raise ValueError(f"lookup mismatch at {row:02x}{cell:02x}")
            tested += 1
    calls.clear()
    uc.reg_write(UC_MIPS_REG_A0, 0x8140); uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
    uc.emu_start(LOOKUP, SENTINEL, count=500)
    fallback = calls[-1]
    if fallback["address"] != "0xb0" or (uc.reg_read(UC_MIPS_REG_T1) & 0xFFFFFFFF) != 0x51:
        raise ValueError("fallback mismatch")
    result = {"pass": True, "artifact_sha256": sha(image), "iso_files": len(disc.files), "dummy_extent_preserved": True, "font_sha256": sha(font), "loader": {"initial_pool": initial_size, "reduced_pool": reduced, "font_base": hex(base), "ready": ready}, "lookup_valid_codes": tested, "fallback": fallback, "edc_ecc_checked_sectors": len(manifest["touched_sectors"]), "limitations": ["Runtime boot and screen verification are separate.", "The isolated SDK calls are mocked at their verified entry ABIs."]}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
