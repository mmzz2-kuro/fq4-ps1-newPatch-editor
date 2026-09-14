#!/usr/bin/env python3
"""Verify the FQ4 map-menu glyph PoC artifact and isolated MIPS paths."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "fq4" / "python-deps"))
sys.path.insert(0, str(ROOT / "tools" / "scripts"))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32  # noqa: E402
from unicorn import Uc, UC_ARCH_MIPS, UC_HOOK_CODE, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32  # noqa: E402
from unicorn.mips_const import (  # noqa: E402
    UC_MIPS_REG_A0,
    UC_MIPS_REG_A1,
    UC_MIPS_REG_A2,
    UC_MIPS_REG_RA,
    UC_MIPS_REG_T1,
    UC_MIPS_REG_T2,
    UC_MIPS_REG_V0,
)

from survey_rom import Disc  # noqa: E402


ROM = ROOT / "work" / "fq4" / "rom" / "current.bin"
REPORT = ROOT / "docs" / "fq4" / "analysis" / "004" / "poc-build.json"
OUTPUT = ROOT / "docs" / "fq4" / "analysis" / "004" / "poc-verification.json"
HOOK = 0x80082C8C
CONVERT = 0x80046674
SENTINEL = 0x801F0000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def static_convert(glyph: bytes) -> bytes:
    result = bytearray()
    for y in range(15):
        pixels = [1 if glyph[y * 2 + x // 8] & (0x80 >> (x % 8)) else 0 for x in range(16)]
        result.extend(pixels[x] | pixels[x + 1] << 4 for x in range(0, 16, 2))
    result.extend(bytes(8))
    return bytes(result)


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    image = ROM.read_bytes()
    if sha(image) != report["output_sha256"]:
        raise ValueError("menu PoC output identity mismatch")
    disc = Disc(ROM)
    record = next(item for item in disc.files if item["path"] == "/SLPS_006.04;1")
    exe = disc.read(record)
    if len(exe) != 1_075_200 or not exe.startswith(b"PS-X EXE"):
        raise ValueError("executable structure mismatch")

    uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(0, 0x200000)
    uc.mem_write(0x10000, exe[0x800:])
    custom = []
    for glyph in report["glyphs"]:
        code = int(glyph["code"], 16)
        expected_pointer = int(glyph["ram"], 16)
        uc.reg_write(UC_MIPS_REG_A0, code)
        uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
        uc.emu_start(HOOK, SENTINEL, count=500)
        pointer = uc.reg_read(UC_MIPS_REG_V0) & 0xFFFFFFFF
        if pointer != expected_pointer:
            raise ValueError(f"wrong glyph pointer for {code:04X}: {pointer:08X}")
        glyph_bytes = bytes(uc.mem_read(pointer & 0x1FFFFFFF, 30))
        if sha(glyph_bytes) != glyph["glyph_sha256"]:
            raise ValueError(f"glyph hash mismatch for {code:04X}")
        destination = 0x801E0000
        uc.mem_write(destination & 0x1FFFFFFF, bytes(128))
        uc.reg_write(UC_MIPS_REG_A0, destination)
        uc.reg_write(UC_MIPS_REG_A1, pointer)
        uc.reg_write(UC_MIPS_REG_A2, 0)
        uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
        uc.emu_start(CONVERT, SENTINEL, count=10000)
        converted = bytes(uc.mem_read(destination & 0x1FFFFFFF, 128))
        expected = static_convert(glyph_bytes)
        if converted != expected:
            raise ValueError(f"converter mismatch for {code:04X}")
        custom.append({"character": glyph["character"], "code": glyph["code"], "returned": hex(pointer), "converted_sha256": sha(converted), "matches_static_decode": True})

    fallback = []

    def on_code(mu: Uc, address: int, size: int, user: object) -> None:
        if address == 0xB0:
            fallback.append({"pc": hex(address), "a0": hex(mu.reg_read(UC_MIPS_REG_A0)), "t1": hex(mu.reg_read(UC_MIPS_REG_T1)), "t2": hex(mu.reg_read(UC_MIPS_REG_T2))})
            mu.emu_stop()

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_MIPS_REG_A0, 0x8140)
    uc.reg_write(UC_MIPS_REG_RA, SENTINEL)
    uc.emu_start(HOOK, SENTINEL, count=500)
    expected_fallback = [{"pc": "0xb0", "a0": "0x8140", "t1": "0x51", "t2": "0xb0"}]
    if fallback != expected_fallback:
        raise ValueError(f"fallback mismatch: {fallback}")

    code_address = int(report["code"]["ram"], 16)
    code_length = int(report["code"]["length"])
    code_bytes = bytes(uc.mem_read(code_address & 0x1FFFFFFF, code_length))
    instructions = list(Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN).disasm(code_bytes, code_address))
    for index, instruction in enumerate(instructions[:-1]):
        if instruction.mnemonic in ("lb", "lbu", "lh", "lhu", "lw") and instructions[index + 1].mnemonic != "nop":
            raise ValueError(f"load delay slot is not protected after {instruction.address:08X}")
    menu_strings = json.loads((ROOT / "docs" / "fq4" / "analysis" / "004" / "menu-strings.json").read_text(encoding="utf-8"))
    for string in menu_strings["strings"]:
        sequence = bytes.fromhex(string["game_code_hex"])
        if not any(sequence in exe for _ in [0]):
            raise ValueError(f"menu string disappeared: {string['text']}")

    output = {
        "artifact_sha256": sha(image),
        "evidence_class": "artifact verification and isolated MIPS execution; visual runtime is separate",
        "custom_results": custom,
        "fallback": fallback,
        "instruction_count": len(instructions),
        "instructions": [{"address": hex(item.address), "bytes": item.bytes.hex(), "mnemonic": item.mnemonic, "operands": item.op_str} for item in instructions],
        "iso_file_records": len(disc.files),
        "target_string_count": len(menu_strings["strings"]),
        "unique_glyph_count": len(custom),
        "pass": True,
        "limitations": ["No final screen pixels were observed in this verifier.", "The development zero region is not established as product-safe."],
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact_sha256": output["artifact_sha256"], "glyphs": len(custom), "instructions": len(instructions), "fallback": fallback, "pass": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
