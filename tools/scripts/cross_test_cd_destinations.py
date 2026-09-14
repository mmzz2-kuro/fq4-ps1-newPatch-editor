#!/usr/bin/env python3
"""Run one PLAN-009 CD sector/destination cross-test through DuckStation GDB."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import time
from pathlib import Path

from gdb_runtime_probe import GDB

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "work/fq4/rom/current.bin"
WRAPPER = 0x8008F600
LOW_BUFFER = 0x801179BC
HIGH_BUFFER = 0x801E6528


def registers(gdb: GDB) -> list[int]:
    raw = bytes.fromhex(gdb.cmd("g")[:256])
    return [struct.unpack_from("<I", raw, index * 4)[0] for index in range(32)]


def read_memory(gdb: GDB, address: int, size: int) -> bytes:
    result = bytearray()
    while len(result) < size:
        count = min(0x400, size - len(result))
        reply = gdb.cmd(f"m{address + len(result):x},{count:x}")
        if reply.startswith("E"):
            raise RuntimeError(f"memory read failed: {reply}")
        result.extend(bytes.fromhex(reply))
    return bytes(result)


def set_register(gdb: GDB, index: int, value: int) -> None:
    reply = gdb.cmd(f"P{index:x}={struct.pack('<I', value).hex()}")
    if reply != "OK":
        raise RuntimeError(f"register write failed: {reply}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("A", "B", "C", "D"))
    parser.add_argument("--candidate", type=lambda value: int(value, 0), default=LOW_BUFFER)
    parser.add_argument("--logical-lba", type=lambda value: int(value, 0))
    parser.add_argument("--match-lba", type=lambda value: int(value, 0))
    args = parser.parse_args()

    logical_lba = args.logical_lba if args.logical_lba is not None else (16 if args.case in ("A", "B") else 24034)
    destination = {
        "A": LOW_BUFFER,
        "B": HIGH_BUFFER,
        "C": LOW_BUFFER,
        "D": args.candidate,
    }[args.case]
    raw_lba = logical_lba + 150
    match_lba = args.match_lba if args.match_lba is not None else logical_lba
    # The wrapper's sector argument addresses sectors in the BIN directly.  The
    # raw_lba name is retained in the report for compatibility with PLAN-008.
    raw_lba = logical_lba
    rom = ROM.read_bytes()
    expected = rom[raw_lba * 2352 + 24:raw_lba * 2352 + 2072]

    deadline = time.time() + 25
    while True:
        try:
            gdb = GDB("127.0.0.1", 2345)
            break
        except OSError:
            if time.time() >= deadline:
                raise
            time.sleep(0.2)
    gdb.cmd("qSupported")
    gdb.cmd("?")
    if gdb.cmd(f"Z0,{WRAPPER:x},4") != "OK":
        raise RuntimeError("could not install wrapper breakpoint")
    gdb.s.settimeout(40)

    hits = 0
    while True:
        stop = gdb.cmd("c")
        regs = registers(gdb)
        hits += 1
        if regs[4] == 1 and regs[5] == match_lba:
            entry = {"a0": regs[4], "a1": regs[5], "a2_before": regs[6], "ra": regs[31]}
            set_register(gdb, 6, destination)
            set_register(gdb, 5, logical_lba)
            return_address = regs[31]
            if gdb.cmd(f"Z0,{return_address:x},4") != "OK":
                raise RuntimeError("could not install return breakpoint")
            gdb.cmd(f"z0,{WRAPPER:x},4")
            return_stop = gdb.cmd("c")
            data = read_memory(gdb, destination, 2048)
            break
        if hits > 256:
            raise RuntimeError("target CD call not reached")

    report = {
        "case": args.case,
        "entry_stop": stop,
        "return_stop": return_stop,
        "logical_lba": logical_lba,
        "raw_lba": raw_lba,
        "destination": hex(destination),
        "entry": {key: hex(value) for key, value in entry.items()},
        "expected_sha256": hashlib.sha256(expected).hexdigest(),
        "actual_sha256": hashlib.sha256(data).hexdigest(),
        "equal": data == expected,
        "expected_head": expected[:64].hex(),
        "actual_head": data[:64].hex(),
        "wrapper_hits": hits,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
