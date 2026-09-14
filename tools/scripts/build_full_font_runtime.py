#!/usr/bin/env python3
"""Install the FQ4 full Hangul font loader into the single reusable work ROM."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "fq4" / "python-deps"))
sys.path.insert(0, str(ROOT / "tools" / "scripts"))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32  # noqa: E402
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_LITTLE_ENDIAN, KS_MODE_MIPS32  # noqa: E402
from build_bios_independent_poc import EXE_HEADER, EXE_LBA, EXE_SIZE, LOAD, fix_form1  # noqa: E402

ROM = ROOT / "work" / "fq4" / "rom" / "current.bin"
BIOS = ROOT / "korean-patch" / "SCPH1001.BIN"
OUT = ROOT / "docs" / "fq4" / "analysis" / "010"
START_SHA = "1911cfe9d9ca963a2761414c5df0881115759628ffdea637c97f8dbf62da3b86"
BIOS_SHA = "f8658d98e32c6a8560a832c50f74f84662e1bff98c486c6480c207a2b404b88f"
DUMMY_LBA = 24184
FONT_BIOS_OFF = 0x69D68
FONT_BYTES = 70500
FONT_SECTORS = 35
FONT_RESERVE = 0x11800
CODE_START = 0x800ECC40
LOOKUP = 0x800ECD80
GLOBALS = 0x800ECF40  # +0 font_base, +4 ready
LOC = 0x800ECF48
REGION_END = 0x800ECF50
KROM_HOOK = 0x80082C8C
INIT_CALL = 0x80013A38
ORIGINAL_POOL_INIT = 0x8004A61C
CD_CONTROL = 0x8008C204
CD_READ = 0x8008E1FC
CD_READ_SYNC = 0x8008E5AC
GAME_CD_READ = 0x8008F600
GAME_CD_DATA_SYNC = 0x8008C648
MAGIC = b"FQ4F"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exe_off(address: int) -> int:
    return address - LOAD + EXE_HEADER


def asm(source: str, address: int) -> bytes:
    return bytes(Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 | KS_MODE_LITTLE_ENDIAN).asm(source, addr=address, as_bytes=True)[0])


def main() -> None:
    if sha(ROM.read_bytes()) != START_SHA or sha(BIOS.read_bytes()) != BIOS_SHA:
        raise ValueError("input identity mismatch")
    image = bytearray(ROM.read_bytes())
    baseline = bytes(image)
    exe = bytearray().join(image[(EXE_LBA + i) * 2352 + 24:(EXE_LBA + i) * 2352 + 2072] for i in range((EXE_SIZE + 2047) // 2048))[:EXE_SIZE]
    bios = BIOS.read_bytes()
    font = bios[FONT_BIOS_OFF:FONT_BIOS_OFF + FONT_BYTES]
    if len(font) != FONT_BYTES:
        raise ValueError("font extraction failed")

    wrapper_src = f"""
        addiu $sp, $sp, -0x30
        sw $ra, 0x2c($sp)
        sw $s0, 0x28($sp)
        sw $s1, 0x24($sp)
        sw $s2, 0x20($sp)
        lui $s0, 0x800e
        ori $s0, $s0, 0xcf40
        sw $zero, 4($s0)
        lui $t0, 0x8011
        lw $t1, 0x59fc($t0)
        nop
        lui $t2, 1
        ori $t2, $t2, 0x1800
        subu $t1, $t1, $t2
        sw $t1, 0x59fc($t0)
        lw $t3, 0x5c10($t0)
        nop
        addu $t4, $t3, $t1
        sw $t4, 0($s0)
        jal 0x{ORIGINAL_POOL_INIT:08x}
        nop
        move $s1, $zero
        lw $s2, 0($s0)
        nop
    sector_loop:
        addiu $a0, $zero, 1
        ori $a1, $zero, 0x{DUMMY_LBA:04x}
        addu $a1, $a1, $s1
        move $a2, $s2
        jal 0x{GAME_CD_READ:08x}
        nop
        beqz $v0, load_fail
        nop
        addiu $s1, $s1, 1
        addiu $s2, $s2, 0x800
        slti $t0, $s1, 35
        bnez $t0, sector_loop
        nop
        lw $t0, 0($s0)
        nop
        lui $t1, 1
        ori $t1, $t1, 0x1364
        addu $t0, $t0, $t1
        lw $t1, 0($t0)
        lui $t2, 0x4634
        ori $t2, $t2, 0x5146
        bne $t1, $t2, load_fail
        nop
        addiu $t0, $zero, 1
        sw $t0, 4($s0)
    load_fail:
        lw $ra, 0x2c($sp)
        lw $s0, 0x28($sp)
        lw $s1, 0x24($sp)
        lw $s2, 0x20($sp)
        addiu $sp, $sp, 0x30
        jr $ra
        nop
    """
    lookup_src = """
        lui $t7, 0x800e
        ori $t7, $t7, 0xcf40
        lw $t6, 4($t7)
        nop
        beqz $t6, fallback
        nop
        srl $t0, $a0, 8
        andi $t1, $a0, 0xff
        sltiu $t2, $t0, 0x81
        bnez $t2, fallback
        nop
        sltiu $t2, $t0, 0xa0
        bnez $t2, lead_low
        nop
        sltiu $t2, $t0, 0xe0
        bnez $t2, fallback
        nop
        sltiu $t2, $t0, 0xf0
        beqz $t2, fallback
        nop
        addiu $t0, $t0, -0xc1
        b lead_done
        nop
    lead_low:
        addiu $t0, $t0, -0x81
    lead_done:
        sll $t0, $t0, 1
        addiu $t0, $t0, 0x21
        sltiu $t2, $t1, 0x40
        bnez $t2, fallback
        nop
        sltiu $t2, $t1, 0x7f
        bnez $t2, trail_low
        nop
        addiu $t2, $zero, 0x7f
        beq $t1, $t2, fallback
        nop
        sltiu $t2, $t1, 0x9f
        bnez $t2, trail_mid
        nop
        sltiu $t2, $t1, 0xfd
        beqz $t2, fallback
        nop
        addiu $t0, $t0, 1
        addiu $t1, $t1, -0x7e
        b range_check
        nop
    trail_low:
        addiu $t1, $t1, -0x1f
        b range_check
        nop
    trail_mid:
        addiu $t1, $t1, -0x20
    range_check:
        sltiu $t2, $t0, 0x30
        bnez $t2, fallback
        nop
        sltiu $t2, $t0, 0x49
        beqz $t2, fallback
        nop
        sltiu $t2, $t1, 0x21
        bnez $t2, fallback
        nop
        sltiu $t2, $t1, 0x7f
        beqz $t2, fallback
        nop
        addiu $t0, $t0, -0x30
        addiu $t1, $t1, -0x21
        sll $t2, $t0, 6
        sll $t3, $t0, 5
        addu $t2, $t2, $t3
        sll $t3, $t0, 1
        subu $t0, $t2, $t3
        addu $t0, $t0, $t1
        sll $t2, $t0, 5
        sll $t3, $t0, 1
        subu $t0, $t2, $t3
        lw $v0, 0($t7)
        nop
        addu $v0, $v0, $t0
        jr $ra
        nop
    fallback:
        addiu $t2, $zero, 0xb0
        addiu $t1, $zero, 0x51
        jr $t2
        nop
    """
    wrapper = asm(wrapper_src, CODE_START)
    lookup = asm(lookup_src, LOOKUP)
    if CODE_START + len(wrapper) > LOOKUP or LOOKUP + len(lookup) > GLOBALS:
        raise ValueError(f"code layout overflow: wrapper={len(wrapper)} lookup={len(lookup)}")

    expected_init = asm(f"jal 0x{ORIGINAL_POOL_INIT:08x}", INIT_CALL)
    if bytes(exe[exe_off(INIT_CALL):exe_off(INIT_CALL) + 4]) != expected_init[:4]:
        raise ValueError("pool init call identity mismatch")
    if exe_off(REGION_END) > len(exe):
        raise ValueError("code region outside executable")
    region = bytearray(REGION_END - CODE_START)
    region[:len(wrapper)] = wrapper
    lo = LOOKUP - CODE_START
    region[lo:lo + len(lookup)] = lookup
    loc_off = LOC - CODE_START
    # GAME_CD_READ takes the sector index in the BIN. It adds the 150-frame
    # lead-in internally while converting that index to CdlLOC.
    frame = DUMMY_LBA + 150
    minute, remain = divmod(frame, 75 * 60)
    second, frame = divmod(remain, 75)
    bcd = lambda value: (value // 10) * 16 + value % 10
    region[loc_off:loc_off + 4] = bytes((bcd(minute), bcd(second), bcd(frame), 0x00))

    writes = []
    def put(name: str, offset: int, data: bytes) -> None:
        before = bytes(exe[offset:offset + len(data)])
        exe[offset:offset + len(data)] = data
        writes.append({"name": name, "exe_offset": hex(offset), "ram": hex(LOAD + offset - EXE_HEADER), "length": len(data), "before_sha256": sha(before), "after_sha256": sha(data)})

    put("runtime_code_and_globals", exe_off(CODE_START), bytes(region))
    put("pool_init_call", exe_off(INIT_CALL), asm(f"jal 0x{CODE_START:08x}", INIT_CALL))
    put("krom_lookup_hook", exe_off(KROM_HOOK), asm(f"j 0x{LOOKUP:08x}", KROM_HOOK))

    touched = set(range(DUMMY_LBA, DUMMY_LBA + FONT_SECTORS))
    for item in writes:
        start = int(item["exe_offset"], 16)
        for pos in range(start, start + int(item["length"])):
            lba = EXE_LBA + pos // 2048
            image[lba * 2352 + 24 + pos % 2048] = exe[pos]
            touched.add(lba)

    payload = font + MAGIC + struct.pack("<III", 1, 2350, FONT_BYTES)
    payload = payload.ljust(FONT_SECTORS * 2048, b"\0")
    for index in range(FONT_SECTORS):
        lba = DUMMY_LBA + index
        image[lba * 2352 + 24:lba * 2352 + 2072] = payload[index * 2048:(index + 1) * 2048]

    sector_audit = []
    for lba in sorted(touched):
        off = lba * 2352
        before = bytearray(baseline[off:off + 2352])
        check = bytearray(before); fix_form1(check)
        if check != before:
            raise ValueError(f"baseline EDC/ECC invalid at {lba}")
        after = bytearray(image[off:off + 2352]); fix_form1(after)
        image[off:off + 2352] = after
        sector_audit.append({"lba": lba, "before_sha256": sha(before), "after_sha256": sha(after)})
    diff = [lba for lba in range(len(image) // 2352) if image[lba * 2352:(lba + 1) * 2352] != baseline[lba * 2352:(lba + 1) * 2352]]
    if diff != sorted(touched):
        raise ValueError("unregistered sector change")
    for lba in touched:
        off = lba * 2352
        if image[off:off + 24] != baseline[off:off + 24]:
            raise ValueError("protected header changed")

    OUT.mkdir(parents=True, exist_ok=True)
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    report = {
        "status": "built_pending_runtime_verification",
        "input_sha256": START_SHA,
        "output_sha256": sha(image),
        "output_size": len(image),
        "font": {"source_offset": hex(FONT_BIOS_OFF), "bytes": FONT_BYTES, "sha256": sha(font), "disc_lba": DUMMY_LBA, "sectors": FONT_SECTORS, "magic_offset": FONT_BYTES},
        "ram": {"reserve_bytes": FONT_RESERVE, "font_base_global": hex(GLOBALS), "ready_global": hex(GLOBALS + 4)},
        "functions": {"wrapper": hex(CODE_START), "lookup": hex(LOOKUP), "game_cd_read": hex(GAME_CD_READ), "game_cd_data_sync": hex(GAME_CD_DATA_SYNC), "CdControl": hex(CD_CONTROL), "CdRead": hex(CD_READ), "CdReadSync": hex(CD_READ_SYNC)},
        "code": {"wrapper_bytes": len(wrapper), "lookup_bytes": len(lookup), "wrapper_source": wrapper_src, "lookup_source": lookup_src, "wrapper_disassembly": [f"{i.address:08x}: {i.mnemonic} {i.op_str}" for i in md.disasm(wrapper, CODE_START)], "lookup_disassembly": [f"{i.address:08x}: {i.mnemonic} {i.op_str}" for i in md.disasm(lookup, LOOKUP)]},
        "writes": writes,
        "touched_sectors": sector_audit,
        "raw_diff_sectors": diff,
    }
    tmp = ROM.with_suffix(".bin.tmp")
    tmp.write_bytes(image)
    if sha(tmp.read_bytes()) != report["output_sha256"]:
        tmp.unlink(); raise ValueError("temporary output verification failed")
    os.replace(tmp, ROM)
    (OUT / "build-manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_sha256": report["output_sha256"], "wrapper_bytes": len(wrapper), "lookup_bytes": len(lookup), "touched_sectors": len(diff)}, indent=2))


if __name__ == "__main__":
    main()
