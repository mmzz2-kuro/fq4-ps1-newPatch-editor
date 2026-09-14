#!/usr/bin/env python3
"""Build the FQ4 map-menu glyph PoC into the single reusable work ROM."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "fq4" / "python-deps"))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32  # noqa: E402
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_LITTLE_ENDIAN, KS_MODE_MIPS32  # noqa: E402

from build_bios_independent_poc import (  # noqa: E402
    BASE_SHA,
    BIOS_SHA,
    EXE_HEADER,
    EXE_LBA,
    EXE_SIZE,
    HOOK_RAM,
    LOAD,
    ORIGINAL_SHA,
    file_sha,
    fix_form1,
)


CODE_RAM = 0x800ECC40
TABLE_RAM = 0x800ECCC0
GLYPH_RAM = 0x800ECD00
PRIOR = [(0x8952, 0x6AA88, "교"), (0x8EB5, 0x7242C, "섭"), (0x917E, 0x75FF0, "중")]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exe_off(address: int) -> int:
    return address - LOAD + EXE_HEADER


def assemble(count: int) -> tuple[bytes, str]:
    source = f"""
        lui $t0, 0x800e
        ori $t0, $t0, 0xccc0
        ori $t1, $zero, {count}
    loop:
        lhu $t2, 0($t0)
        nop
        beq $a0, $t2, found
        nop
        addiu $t0, $t0, 4
        addiu $t1, $t1, -1
        bnez $t1, loop
        nop
        addiu $t2, $zero, 0xb0
        addiu $t1, $zero, 0x51
        jr $t2
        nop
    found:
        lhu $v0, 2($t0)
        nop
        sll $t2, $v0, 5
        sll $v0, $v0, 1
        subu $v0, $t2, $v0
        lui $t2, 0x800e
        ori $t2, $t2, 0xcd00
        addu $v0, $v0, $t2
        jr $ra
        nop
    """
    code, _ = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 | KS_MODE_LITTLE_ENDIAN).asm(source, addr=CODE_RAM, as_bytes=True)
    code = bytes(code)
    if len(code) > TABLE_RAM - CODE_RAM:
        raise ValueError(f"lookup code does not fit reserved range: {len(code)} bytes")
    return code, source


def main() -> None:
    glyph_report = json.loads((ROOT / "docs" / "fq4" / "analysis" / "004" / "menu-glyphs.json").read_text(encoding="utf-8"))
    menu = [(int(item["game_code"], 16), int(item["bios_offset"], 16), item["character"]) for item in glyph_report["glyphs"]]
    glyphs = PRIOR + [item for item in menu if item[0] not in {code for code, _, _ in PRIOR}]
    if len(glyphs) != 13 or len({code for code, _, _ in glyphs}) != 13:
        raise ValueError("expected 13 unique prior+menu glyphs")

    original = next((ROOT / "original").glob("*.bin"))
    patch = next((ROOT / "korean-patch").glob("*250826*.xdelta"))
    bios_path = ROOT / "korean-patch" / "SCPH1001.BIN"
    current = ROOT / "work" / "fq4" / "rom" / "current.bin"
    if file_sha(original) != ORIGINAL_SHA or file_sha(bios_path) != BIOS_SHA:
        raise ValueError("input identity mismatch")
    subprocess.run([str(ROOT / "korean-patch" / "xdelta.exe"), "-d", "-f", "-s", str(original), str(patch), str(current)], check=True)
    if file_sha(current) != BASE_SHA:
        raise ValueError("250826 baseline mismatch")

    image = bytearray(current.read_bytes())
    baseline = bytes(image)
    bios = bios_path.read_bytes()
    exe = bytearray().join(image[(EXE_LBA + i) * 2352 + 24 : (EXE_LBA + i) * 2352 + 2072] for i in range((EXE_SIZE + 2047) // 2048))[:EXE_SIZE]
    if not exe.startswith(b"PS-X EXE"):
        raise ValueError("executable identity mismatch")

    code, source = assemble(len(glyphs))
    table = b"".join(struct.pack("<HH", code_value, index) for index, (code_value, _, _) in enumerate(glyphs))
    glyph_data = b"".join(bios[offset : offset + 30] for _, offset, _ in glyphs)
    if TABLE_RAM + len(table) > GLYPH_RAM:
        raise ValueError("lookup table overlaps glyph data")
    region_start = exe_off(CODE_RAM)
    region_end = exe_off(GLYPH_RAM) + len(glyph_data)
    if any(exe[region_start:region_end]):
        raise ValueError("menu PoC destination is not zero in 250826 baseline")

    hook = bytes(Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 | KS_MODE_LITTLE_ENDIAN).asm(f"j 0x{CODE_RAM:08x}", addr=HOOK_RAM, as_bytes=True)[0])
    if len(hook) != 8:
        raise ValueError("unexpected hook size")
    expected_hook = bytes.fromhex("b0000a24080040015100092400000000")
    if bytes(exe[exe_off(HOOK_RAM) : exe_off(HOOK_RAM) + 16]) != expected_hook:
        raise ValueError("BIOS wrapper expected bytes mismatch")

    writes: list[dict[str, object]] = []

    def write(name: str, offset: int, data: bytes, condition: str) -> None:
        before = bytes(exe[offset : offset + len(data)])
        writes.append({"writer": name, "offset": hex(offset), "ram": hex(LOAD + offset - EXE_HEADER), "length": len(data), "expected_sha256": sha(before), "final_sha256": sha(data), "source_condition": condition})
        exe[offset : offset + len(data)] = data

    write("glyph_lookup_hook", exe_off(HOOK_RAM), hook, "verified B0(51h) wrapper")
    write("table_lookup_code", exe_off(CODE_RAM), code, "zero-filled development region")
    write("code_to_index_table", exe_off(TABLE_RAM), table, "zero-filled development region")
    write("prior_and_menu_glyphs", exe_off(GLYPH_RAM), glyph_data, "zero-filled development region")

    touched: set[int] = set()
    for entry in writes:
        offset = int(str(entry["offset"]), 16)
        for position in range(offset, offset + int(entry["length"])):
            lba = EXE_LBA + position // 2048
            image[lba * 2352 + 24 + position % 2048] = exe[position]
            touched.add(lba)
    sectors = []
    for lba in sorted(touched):
        start = lba * 2352
        before = bytearray(baseline[start : start + 2352])
        check = bytearray(before)
        fix_form1(check)
        if check != before:
            raise ValueError(f"baseline EDC/ECC invalid at LBA {lba}")
        after = bytearray(image[start : start + 2352])
        fix_form1(after)
        image[start : start + 2352] = after
        sectors.append({"lba": lba, "before_sha256": sha(before), "after_sha256": sha(after)})
    diff_sectors = [lba for lba in range(len(image) // 2352) if image[lba * 2352 : (lba + 1) * 2352] != baseline[lba * 2352 : (lba + 1) * 2352]]
    if diff_sectors != sorted(touched):
        raise ValueError("unregistered changed sector")
    for lba in touched:
        start = lba * 2352
        if image[start : start + 24] != baseline[start : start + 24]:
            raise ValueError("protected sector header changed")

    current.write_bytes(image)
    (ROOT / "work" / "fq4" / "rom" / "current.cue").write_text('FILE "current.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n', encoding="ascii", newline="\r\n")
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    disassembly = [{"address": hex(ins.address), "bytes": ins.bytes.hex(), "mnemonic": ins.mnemonic, "operands": ins.op_str} for ins in md.disasm(code, CODE_RAM)]
    output = {
        "status": "development_menu_poc",
        "baseline_sha256": BASE_SHA,
        "prior_poc_sha256": "e419b4018a8aa02facc3a425ef05f325cb0fc0130e5822015ce43fa2e0baded9",
        "output_sha256": sha(image),
        "output_size": len(image),
        "code": {"ram": hex(CODE_RAM), "length": len(code), "source": source, "disassembly": disassembly},
        "table": {"ram": hex(TABLE_RAM), "length": len(table), "entry_count": len(glyphs), "entry_format": "little-endian uint16 game code, uint16 glyph index"},
        "glyph_data": {"ram": hex(GLYPH_RAM), "length": len(glyph_data)},
        "glyphs": [{"index": index, "character": character, "code": f"{code_value:04X}", "source_bios_offset": hex(offset), "ram": hex(GLYPH_RAM + index * 30), "glyph_sha256": sha(bios[offset : offset + 30])} for index, (code_value, offset, character) in enumerate(glyphs)],
        "writes": writes,
        "touched_sectors": sectors,
        "raw_diff_sectors": diff_sectors,
        "limitations": ["The zero-filled region remains a development PoC placement, not a product-safe allocation.", "Local PoC embeds selected glyph bytes from the supplied BIOS and is not a distributable artifact.", "Visual verification is separate."],
    }
    target = ROOT / "docs" / "fq4" / "analysis" / "004" / "poc-build.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_sha256": output["output_sha256"], "code_bytes": len(code), "table_bytes": len(table), "glyph_bytes": len(glyph_data), "sectors": diff_sectors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
