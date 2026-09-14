#!/usr/bin/env python3
"""Detect the FQ4 Korean-patch executable/ISO structure without version hashes."""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from verify_cdrom_xa_ecc import SYNC, expected_header

SECTOR = 2352
USER_OFFSET = 24
USER_SIZE = 2048
EXPECTED_SIZE = 101_140_704
FONT_SECTORS = 35
LOAD = 0x80010000
CODE_START = 0x800ECC40
REGION_END = 0x800ECF50

INIT_ANCHOR = bytes.fromhex(
    "05004014000000001180023cfc59428c804e000800fc42248729010c00000000"
    "de1a010c000000000a0003341280023c"
)
INIT_DELTA = 0x18
HOOK_ANCHOR = bytes.fromhex(
    "000020000000200000002000b0000a24080040010900092400000000b0000a24"
    "080040015100092400000000010004240c0000000800e00300000000b0000a24"
)
HOOK_DELTA = 0x1C


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def user_sector(image: bytes, lba: int) -> bytes:
    start = lba * SECTOR + USER_OFFSET
    return image[start:start + USER_SIZE]


def root_files(image: bytes) -> dict[str, dict[str, int]]:
    pvd = user_sector(image, 16)
    if pvd[:7] != b"\x01CD001\x01":
        raise ValueError("ISO9660 PVD를 찾을 수 없습니다.")
    root_len = pvd[156]
    root = pvd[156:156 + root_len]
    root_lba = struct.unpack_from("<I", root, 2)[0]
    root_size = struct.unpack_from("<I", root, 10)[0]
    data = b"".join(user_sector(image, lba) for lba in range(root_lba, root_lba + (root_size + USER_SIZE - 1) // USER_SIZE))[:root_size]
    result: dict[str, dict[str, int]] = {}
    pos = 0
    while pos < len(data):
        length = data[pos]
        if not length:
            pos = ((pos // USER_SIZE) + 1) * USER_SIZE
            continue
        record = data[pos:pos + length]
        name_len = record[32]
        name = record[33:33 + name_len].decode("ascii", "replace").split(";", 1)[0]
        if name not in ("\x00", "\x01"):
            result[name] = {
                "lba": struct.unpack_from("<I", record, 2)[0],
                "size": struct.unpack_from("<I", record, 10)[0],
                "flags": record[25],
            }
        pos += length
    return result


def extract_file(image: bytes, entry: dict[str, int]) -> bytes:
    count = (entry["size"] + USER_SIZE - 1) // USER_SIZE
    return b"".join(user_sector(image, entry["lba"] + i) for i in range(count))[:entry["size"]]


def unique(executable: bytes, signature: bytes, label: str) -> int:
    first = executable.find(signature)
    if first < 0:
        raise ValueError(f"호환되지 않는 패치 구조: {label} signature 없음")
    if executable.find(signature, first + 1) >= 0:
        raise ValueError(f"호환되지 않는 패치 구조: {label} signature 중복")
    return first


def lookup_domain_stats(executable: bytes) -> tuple[int, int]:
    values = []
    for lead, trail in zip(executable, executable[1:]):
        if not ((0x81 <= lead < 0xA0) or (0xE0 <= lead < 0xF0)):
            continue
        if not ((0x40 <= trail < 0x7F) or (0x80 <= trail < 0xFD)):
            continue
        row = (lead - 0x81) * 2 + 0x21 if lead < 0xA0 else (lead - 0xC1) * 2 + 0x21
        if trail >= 0x9F:
            row += 1
        if 0x30 <= row < 0x49:
            values.append((lead << 8) | trail)
    return len(values), len(set(values))


def detect(image_path: Path) -> dict[str, object]:
    image = image_path.read_bytes()
    if len(image) != EXPECTED_SIZE or len(image) % SECTOR:
        raise ValueError("호환되지 않는 디스크 크기 또는 raw sector 형식")
    files = root_files(image)
    try:
        exe_entry = files["SLPS_006.04"]
        dummy = files["DUMMY.DUM"]
    except KeyError as exc:
        raise ValueError(f"필수 ISO 파일이 없습니다: {exc.args[0]}") from exc
    if dummy["size"] < FONT_SECTORS * USER_SIZE:
        raise ValueError("DUMMY.DUM에 글꼴용 연속 sector 공간이 부족합니다.")
    executable = extract_file(image, exe_entry)
    if not executable.startswith(b"PS-X EXE"):
        raise ValueError("SLPS_006.04가 PS-X EXE 형식이 아닙니다.")
    load = struct.unpack_from("<I", executable, 0x18)[0]
    declared_size = struct.unpack_from("<I", executable, 0x1C)[0]
    if load != LOAD or declared_size + 0x800 != len(executable):
        raise ValueError("실행 파일 load address 또는 크기가 호환되지 않습니다.")
    init_anchor = unique(executable, INIT_ANCHOR, "pool init")
    hook_anchor = unique(executable, HOOK_ANCHOR, "BIOS glyph wrapper")
    cave_start = CODE_START - load + 0x800
    cave_end = REGION_END - load + 0x800
    if cave_start < 0 or cave_end > len(executable) or any(executable[cave_start:cave_end]):
        raise ValueError("호환되지 않는 패치 구조: loader code 영역이 비어 있지 않습니다.")
    domain_pairs, domain_unique = lookup_domain_stats(executable)
    if domain_pairs < 1000 or domain_unique < 500:
        raise ValueError("호환되지 않는 패치 구조: 기존 Shift-JIS 위치 기반 문자 domain을 확인할 수 없습니다.")
    return {
        "profile": "fq4-korean-sjis-v1",
        "image_sha256": sha256(image),
        "size": len(image),
        "exe_lba": exe_entry["lba"],
        "exe_size": exe_entry["size"],
        "exe_sha256": sha256(executable),
        "load_address": load,
        "dummy_lba": dummy["lba"],
        "dummy_size": dummy["size"],
        "init_call": load + init_anchor + INIT_DELTA - 0x800,
        "krom_hook": load + hook_anchor + HOOK_DELTA - 0x800,
        "code_start": CODE_START,
        "region_end": REGION_END,
        "lookup_domain_pairs": domain_pairs,
        "lookup_domain_unique_codes": domain_unique,
    }


def validate_sector_envelope(image_path: Path) -> dict[str, int]:
    """Reject damaged sync/address/XA metadata without treating stale ECC as structural."""
    failures = {"sync": 0, "header": 0, "subheader": 0}
    form1 = form2 = 0
    with image_path.open("rb") as stream:
        for lba in range(image_path.stat().st_size // SECTOR):
            sector = stream.read(SECTOR)
            if sector[:12] != SYNC:
                failures["sync"] += 1
                continue
            if sector[12:16] != expected_header(lba):
                failures["header"] += 1
            if sector[15] == 2:
                if sector[16:20] != sector[20:24]:
                    failures["subheader"] += 1
                if sector[18] & 0x20:
                    form2 += 1
                else:
                    form1 += 1
    if any(failures.values()):
        raise ValueError(f"호환되지 않는 raw sector header 구조: {failures}")
    return {"form1": form1, "form2": form2, **failures}


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = detect(args.image)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text, end="")
