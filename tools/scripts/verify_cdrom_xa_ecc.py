#!/usr/bin/env python3
"""Independently audit raw 2352-byte CD-ROM XA sector structure and parity."""

from __future__ import annotations

import argparse
import json
import os
import struct
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SYNC = bytes.fromhex("00ffffffffffffffffffff00")


def tables() -> tuple[list[int], list[int], list[int]]:
    edc_lut, forward, backward = [], [0] * 256, [0] * 256
    for value in range(256):
        x = value
        for _ in range(8):
            x = (x >> 1) ^ 0xD8018001 if x & 1 else x >> 1
        edc_lut.append(x & 0xFFFFFFFF)
        y = ((value << 1) ^ (0x11D if value & 0x80 else 0)) & 0xFF
        forward[value] = y
        backward[value ^ y] = value
    return edc_lut, forward, backward


EDC_LUT, ECC_F, ECC_B = tables()


def edc(data: bytes) -> int:
    value = 0
    for byte in data:
        value = (value >> 8) ^ EDC_LUT[(value ^ byte) & 0xFF]
    return value & 0xFFFFFFFF


def parity(source: bytes, major_count: int, minor_count: int, major_mult: int, minor_inc: int) -> bytes:
    size = major_count * minor_count
    result = bytearray(major_count * 2)
    for major in range(major_count):
        index = ((major >> 1) * major_mult + (major & 1)) % size
        a = b = 0
        for _ in range(minor_count):
            value = source[index]
            index = (index + minor_inc) % size
            a ^= value
            b ^= value
            a = ECC_F[a]
        a = ECC_B[ECC_F[a] ^ b]
        result[major] = a
        result[major + major_count] = a ^ b
    return bytes(result)


def expected_form1(sector: bytes) -> tuple[bytes, bytes, bytes]:
    expected_edc = struct.pack("<I", edc(sector[16:2072]))
    # ECMA-130 Annex A treats the address bytes as zero for Mode 2 ECC.
    q_source = b"\0\0\0\0" + sector[16:2072] + expected_edc
    p = parity(q_source, 86, 24, 2, 86)
    q = parity(q_source + p, 52, 43, 86, 88)
    return expected_edc, p, q


def bcd(value: int) -> int:
    return (value // 10) * 16 + value % 10


def expected_header(lba: int) -> bytes:
    frame = lba + 150
    minute, remain = divmod(frame, 75 * 60)
    second, frame = divmod(remain, 75)
    return bytes((bcd(minute), bcd(second), bcd(frame), 2))


def audit_range(job: tuple[str, int, int]) -> dict[str, object]:
    filename, start, end = job
    failures: dict[str, list[int]] = {name: [] for name in ("sync", "header", "subheader", "edc", "p", "q")}
    counts = {"sectors": 0, "mode2_form1": 0, "mode2_form2": 0, "other": 0}
    with open(filename, "rb") as stream:
        stream.seek(start * 2352)
        for lba in range(start, end):
            sector = stream.read(2352)
            counts["sectors"] += 1
            if sector[:12] != SYNC:
                failures["sync"].append(lba)
                counts["other"] += 1
                continue
            if sector[12:16] != expected_header(lba):
                failures["header"].append(lba)
            if sector[15] != 2:
                counts["other"] += 1
                continue
            if sector[16:20] != sector[20:24]:
                failures["subheader"].append(lba)
            if sector[18] & 0x20:
                counts["mode2_form2"] += 1
                continue
            counts["mode2_form1"] += 1
            expected_edc, expected_p, expected_q = expected_form1(sector)
            if sector[2072:2076] != expected_edc:
                failures["edc"].append(lba)
            if sector[2076:2248] != expected_p:
                failures["p"].append(lba)
            if sector[2248:2352] != expected_q:
                failures["q"].append(lba)
    return {"counts": counts, "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    image = args.image.resolve()
    if image.stat().st_size % 2352:
        raise SystemExit("image size is not divisible by 2352")
    total = image.stat().st_size // 2352
    chunk = (total + args.workers - 1) // args.workers
    jobs = [(str(image), start, min(total, start + chunk)) for start in range(0, total, chunk)]
    counts = {"sectors": 0, "mode2_form1": 0, "mode2_form2": 0, "other": 0}
    failures = {name: [] for name in ("sync", "header", "subheader", "edc", "p", "q")}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for part in pool.map(audit_range, jobs):
            for name, value in part["counts"].items():
                counts[name] += value
            for name, values in part["failures"].items():
                failures[name].extend(values)
    for values in failures.values():
        values.sort()
    bad = sorted(set().union(*failures.values()))
    result = {"image": str(image), "size": image.stat().st_size, "counts": counts, "failure_counts": {name: len(values) for name, values in failures.items()}, "failures": failures, "bad_sector_count": len(bad), "bad_sectors": bad}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text, end="")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
