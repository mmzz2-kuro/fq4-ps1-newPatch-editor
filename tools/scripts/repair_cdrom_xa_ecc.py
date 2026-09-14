#!/usr/bin/env python3
"""Repair invalid Mode 2 Form 1 EDC/P/Q tails in one raw BIN atomically."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from verify_cdrom_xa_ecc import expected_form1


def repair_range(job: tuple[str, int, int]) -> list[tuple[int, bytes]]:
    filename, start, end = job
    repairs = []
    with open(filename, "rb") as stream:
        stream.seek(start * 2352)
        for lba in range(start, end):
            sector = stream.read(2352)
            if sector[15] != 2 or sector[16:20] != sector[20:24] or sector[18] & 0x20:
                continue
            edc, p, q = expected_form1(sector)
            tail = edc + p + q
            if sector[2072:2352] != tail:
                repairs.append((lba, tail))
    return repairs


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repair_image(image: Path, workers: int | None = None, start_lba: int = 0, end_lba: int | None = None) -> dict[str, object]:
    image = image.resolve()
    if image.stat().st_size % 2352:
        raise ValueError("image size is not divisible by 2352")
    total = image.stat().st_size // 2352
    end_lba = total if end_lba is None else min(total, end_lba)
    if not 0 <= start_lba <= end_lba:
        raise ValueError("invalid repair LBA range")
    workers = workers or min(8, os.cpu_count() or 1)
    span = end_lba - start_lba
    chunk = max(1, (span + workers - 1) // workers)
    jobs = [(str(image), start, min(end_lba, start + chunk)) for start in range(start_lba, end_lba, chunk)]
    repairs: list[tuple[int, bytes]] = []
    if workers == 1:
        for job in jobs:
            repairs.extend(repair_range(job))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for part in pool.map(repair_range, jobs):
                repairs.extend(part)
    repairs.sort(key=lambda item: item[0])
    before = sha256(image)
    if repairs:
        temp = image.with_name(f".{image.name}.ecc-repair.tmp")
        if temp.exists():
            temp.unlink()
        try:
            with image.open("rb") as source, temp.open("wb") as destination:
                for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
                    destination.write(block)
            with temp.open("r+b") as stream:
                for lba, tail in repairs:
                    stream.seek(lba * 2352 + 2072)
                    stream.write(tail)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, image)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    return {
        "input_sha256": before, "output_sha256": sha256(image),
        "repaired_sector_count": len(repairs),
        "first_repaired_lba": repairs[0][0] if repairs else None,
        "last_repaired_lba": repairs[-1][0] if repairs else None,
        "scan_range": [start_lba, end_lba],
        "repaired_lbas": [lba for lba, _ in repairs],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = repair_image(args.image, args.workers)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "repaired_lbas"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
