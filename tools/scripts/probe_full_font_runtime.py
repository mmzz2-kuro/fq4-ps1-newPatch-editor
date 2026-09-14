#!/usr/bin/env python3
"""Read-only DuckStation GDB probe for the installed full FQ4 font."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from gdb_runtime_probe import GDB
from build_full_font_runtime import BIOS, FONT_BIOS_OFF

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "fq4" / "analysis" / "010" / "runtime-glyph-trace.json"
FONT_BYTES = 70500


def read(gdb: GDB, address: int, size: int) -> bytes:
    result = bytearray()
    while len(result) < size:
        count = min(0x1000, size - len(result))
        reply = gdb.cmd(f"m{address + len(result):x},{count:x}")
        if reply.startswith("E"): raise RuntimeError(reply)
        result.extend(bytes.fromhex(reply))
    return bytes(result)


def main() -> None:
    deadline = time.time() + 20
    last = None
    while time.time() < deadline:
        try:
            g = GDB("127.0.0.1", 2345); break
        except OSError as exc:
            last = exc; time.sleep(0.25)
    else: raise RuntimeError(f"GDB unavailable: {last}")
    supported = g.cmd("qSupported")
    stop = g.cmd("?")
    base = int.from_bytes(read(g, 0x800ECF40, 4), "little")
    ready = int.from_bytes(read(g, 0x800ECF44, 4), "little")
    font = read(g, base, FONT_BYTES) if 0x80180000 <= base < 0x80200000 else b""
    magic = read(g, base + FONT_BYTES, 16) if font else b""
    expected_sha = hashlib.sha256(BIOS.read_bytes()[FONT_BIOS_OFF:FONT_BIOS_OFF + FONT_BYTES]).hexdigest()
    result = {"supported": supported, "stop": stop, "font_base": hex(base), "font_ready": ready, "font_bytes": len(font), "font_sha256": hashlib.sha256(font).hexdigest() if font else None, "expected_sha256": expected_sha, "trailer_hex": magic.hex(), "pass": ready == 1 and hashlib.sha256(font).hexdigest() == expected_sha}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["pass"]: raise SystemExit(1)


if __name__ == "__main__": main()
