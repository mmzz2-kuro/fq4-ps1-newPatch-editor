#!/usr/bin/env python3
"""Invoke the real FQ4 menu glyph upload path under normal BIOS via GDB."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from gdb_runtime_probe import GDB


ROOT = Path(__file__).resolve().parents[2]
HOOK = 0x80082C8C
RENDER = 0x800464C0
LOADIMAGE = 0x800845FC
REPORT = ROOT / "docs" / "fq4" / "analysis" / "004" / "poc-verification.json"
OUTPUT = ROOT / "docs" / "fq4" / "analysis" / "010" / "runtime-glyph-trace.json"


def u32(raw: bytes, number: int) -> int:
    return struct.unpack_from("<I", raw, number * 4)[0]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registers(gdb: GDB) -> bytearray:
    packet = gdb.cmd("g")
    prefix = packet[: 38 * 8]
    if any(character not in "0123456789abcdefABCDEF" for character in prefix):
        raise RuntimeError("core register packet contains unavailable values")
    return bytearray.fromhex(prefix)


def set_register(gdb: GDB, number: int, value: int) -> None:
    reply = gdb.cmd(f"P{number:x}=" + struct.pack("<I", value & 0xFFFFFFFF).hex())
    if reply != "OK":
        raise RuntimeError(f"register {number} write failed: {reply}")


def main() -> None:
    verification = json.loads(REPORT.read_text(encoding="utf-8"))
    codes = [int(item["code"], 16) for item in verification["custom_results"]]
    expected = {int(item["code"], 16): item["converted_sha256"] for item in verification["custom_results"]}
    source = b"".join(code.to_bytes(2, "big") for code in codes) + b"\0"

    gdb = GDB("127.0.0.1", 2345)
    gdb.cmd("qSupported")
    gdb.cmd("?")
    saved = registers(gdb)
    original_pc = u32(saved, 37)
    original_sp = u32(saved, 29)
    scratch = (original_sp - 0x800) & ~0xF
    saved_memory = bytes.fromhex(gdb.cmd(f"m{scratch:x},{len(source):x}"))
    if gdb.cmd(f"M{scratch:x},{len(source):x}:{source.hex()}") != "OK":
        raise RuntimeError("scratch write failed")

    stops = [HOOK, LOADIMAGE, original_pc]
    for address in stops:
        if gdb.cmd(f"Z0,{address:x},4") != "OK":
            raise RuntimeError(f"breakpoint failed {address:x}")
    set_register(gdb, 4, scratch)
    set_register(gdb, 5, 1)
    set_register(gdb, 31, original_pc)
    set_register(gdb, 37, RENDER)

    hooks = []
    uploads = []
    unrelated_uploads = []
    pending_code = None
    returned = False
    for _ in range(len(codes) * 3 + 10):
        packet = gdb.cmd("c")
        current = registers(gdb)
        pc = u32(current, 37)
        if pc == HOOK:
            pending_code = u32(current, 4)
            hooks.append({"code": hex(pending_code), "ra": hex(u32(current, 31))})
        elif pc == LOADIMAGE:
            rectangle = u32(current, 4)
            data = u32(current, 5)
            rectangle_bytes = bytes.fromhex(gdb.cmd(f"m{rectangle:x},8"))
            glyph = bytes.fromhex(gdb.cmd(f"m{data:x},80"))
            event = {
                "code": hex(pending_code) if pending_code is not None else None,
                "rect_xywh": list(struct.unpack("<4H", rectangle_bytes)),
                "data_sha256": sha(glyph),
                "matches_isolated_conversion": bool(pending_code is not None and pending_code in expected and sha(glyph) == expected[pending_code]),
            }
            if pending_code is None:
                unrelated_uploads.append(event)
            else:
                uploads.append(event)
                pending_code = None
        elif pc == original_pc:
            returned = True
            break
        else:
            raise RuntimeError(f"unexpected stop PC {pc:08x}, packet {packet}")

    if gdb.cmd(f"M{scratch:x},{len(saved_memory):x}:{saved_memory.hex()}") != "OK":
        raise RuntimeError("scratch restore failed")
    for number in list(range(1, 35)) + [37]:
        set_register(gdb, number, u32(saved, number))
    for address in stops:
        gdb.cmd(f"z0,{address:x},4")

    passed = returned and [int(item["code"], 16) for item in hooks] == codes and len(uploads) == len(codes) and all(item["matches_isolated_conversion"] for item in uploads)
    result = {
        "evidence_class": "runtime after explicit CPU-state intervention; not normal-play reachability or screenshot evidence",
        "baseline_pc": hex(original_pc),
        "scratch": hex(scratch),
        "input_codes": [hex(code) for code in codes],
        "hook_events": hooks,
        "upload_events": uploads,
        "unrelated_upload_events_ignored": unrelated_uploads,
        "returned_to_baseline_pc": returned,
        "cpu_registers_and_scratch_restored": True,
        "global_and_gpu_state_restored": False,
        "pass": passed,
        "claim_limit": "Proves actual game lookup, conversion, and LoadImage calls under the selected normal BIOS. It does not prove final pixels or normal-play reachability.",
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit("runtime menu probe failed")


if __name__ == "__main__":
    main()
