#!/usr/bin/env python3
"""Generate PS1 save-editor character/class labels from FQ4 discs.

Character names in the Korean patch are a mixed table: ASCII names stay ASCII,
while some Korean names reuse single-byte halfwidth-kana codes with a custom
font. The custom byte-to-Hangul map is bootstrapped from verified localized
names and the patched executable bytes, then applied to the full 640-entry
name table.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_DISC = ROOT / "original" / "First Queen IV - Varcia Senki (Japan).bin"
PATCHED_DISC = ROOT / "patched" / "First Queen IV - Varcia Senki (kor).bin"
UI = ROOT / "tools" / "FQ4SaveEditor"
ANALYSIS = ROOT / "docs" / "fq4" / "analysis" / "023"
EXE_LBA = 24
EXE_SIZE = 1_075_200
CHARACTER_TABLE = 0xE86B0
CHARACTER_COUNT = 640
CHARACTER_WIDTH = 10
CLASS_COUNT = 220

VERIFIED_KOREAN_NAMES = {
    2: "아이크",
    4: "아이라스",
    9: "아트",
    26: "아레스",
    265: "트리스렌",
}

BASE_CUSTOM_BYTE_MAP = {
    0xA5: "간",
    0xA6: "케",
    0xA7: "고",
    0xA8: "콘",
    0xA9: "그",
    0xAB: "노",
    0xAC: "드",
    0xAD: "르",
    0xAE: "라",
    0xAF: "란",
    0xB1: "람",
    0xB2: "라",
    0xB3: "레",
    0xB4: "렌",
    0xB5: "론",
    0xB6: "르",
    0xB7: "리",
    0xB8: "린",
    0xB9: "모",
    0xBC: "바",
    0xBD: "버",
    0xBE: "본",
    0xBF: "신",
    0xC0: "스",
    0xC1: "시",
    0xC2: "아",
    0xC3: "안",
    0xC4: "에",
    0xC5: "알",
    0xC6: "엘",
    0xC7: "오",
    0xC8: "온",
    0xC9: "올",
    0xCC: "월",
    0xCE: "이",
    0xCF: "인",
    0xD0: "제",
    0xD2: "치",
    0xD3: "카",
    0xD4: "카",
    0xD5: "크",
    0xD6: "크",
    0xD7: "키",
    0xD9: "터",
    0xDA: "톤",
    0xDB: "트",
    0xDC: "파",
    0xDD: "프",
    0xDE: "프",
}

KANA_WORD_OVERRIDES = {
    "アルシンプ": "알신프",
    "アルフレッド": "알프레트",
    "ウォルター": "월터",
    "ウォラス": "월라스",
    "エクター": "헥터",
    "オルグ": "올그",
    "オスカル": "오스칼",
    "オズボーン": "오스본",
    "オリバー": "올리버",
    "カイ": "카이",
    "カート": "카트",
    "カートライト": "카트라이트",
    "ガラ": "가라",
    "ガリバー": "가리버",
    "キース": "키스",
    "キリー": "키리",
    "ギルフォード": "길포드",
    "グリフレッド": "그리프레드",
    "グリーン": "그린",
    "クレイ": "크레이",
    "グレイス": "그레이스",
    "ゲイリー": "게일",
    "ケイロン": "케이론",
    "ゲラン": "게란",
    "ゲレス": "게레스",
    "ゴロンゴ": "고론고",
    "コンラッド": "콘라드",
    "サグ": "사그",
    "サクロン": "사크론",
    "シーグラム": "시그람",
    "ジェイク": "제이크",
    "ジェス": "제스",
    "ジェフ": "제프",
    "ジェフリ": "제프리",
    "シラーノ": "시라노",
    "シレノス": "시레노스",
    "スコット": "스코트",
    "スタッド": "스타드",
    "ストーン": "스톤",
    "スリート": "스리트",
    "ドレイク": "드레이크",
}


def executable(path: Path) -> bytes:
    raw = path.read_bytes()
    sectors = (EXE_SIZE + 2047) // 2048
    return b"".join(
        raw[(EXE_LBA + i) * 2352 + 24 : (EXE_LBA + i) * 2352 + 2072]
        for i in range(sectors)
    )[:EXE_SIZE]


def raw_entry(exe: bytes, start: int, index: int, width: int) -> bytes:
    begin = start + index * width
    return exe[begin : begin + width].split(b"\0", 1)[0].rstrip(b" ")


def decode_cp932(raw: bytes, prefix: str, index: int) -> str:
    text = unicodedata.normalize("NFKC", raw.decode("cp932", "replace")).strip()
    return text or f"{prefix} ID {index}"


def derive_custom_map(patched: bytes) -> dict[int, str]:
    mapping: dict[int, str] = dict(BASE_CUSTOM_BYTE_MAP)
    conflicts: dict[int, set[str]] = {}
    for index, name in VERIFIED_KOREAN_NAMES.items():
        raw = raw_entry(patched, CHARACTER_TABLE, index, CHARACTER_WIDTH)
        letters = list(name)
        if len(raw) != len(letters):
            raise ValueError(f"name {index} byte/letter length mismatch: {raw.hex()} -> {name}")
        for byte, char in zip(raw, letters):
            if byte < 0x80:
                raise ValueError(f"name {index} contains non-custom byte {byte:02X}: {raw.hex()}")
            previous = mapping.setdefault(byte, char)
            if previous != char:
                conflicts.setdefault(byte, {previous}).add(char)
    if conflicts:
        detail = ", ".join(f"{byte:02X}={sorted(chars)}" for byte, chars in sorted(conflicts.items()))
        raise ValueError(f"conflicting custom name-byte map: {detail}")
    original = executable(ORIGINAL_DISC)
    for index in range(CHARACTER_COUNT):
        original_name = decode_cp932(raw_entry(original, CHARACTER_TABLE, index, CHARACTER_WIDTH), "Name", index)
        korean = KANA_WORD_OVERRIDES.get(original_name)
        if not korean:
            continue
        raw = raw_entry(patched, CHARACTER_TABLE, index, CHARACTER_WIDTH)
        letters = list(korean)
        if len(raw) != len(letters) or any(byte < 0x80 for byte in raw):
            continue
        candidate = dict(zip(raw, letters))
        if any(byte in mapping and mapping[byte] != char for byte, char in candidate.items()):
            continue
        for byte, char in candidate.items():
            mapping[byte] = char
    return mapping


def decode_patched_name(
    raw: bytes, original_name: str, custom_map: dict[int, str], index: int
) -> tuple[str, str]:
    if not raw:
        return original_name, "fallback-empty"
    out: list[str] = []
    custom = False
    unknown: list[str] = []
    for byte in raw:
        if byte < 0x80:
            out.append(chr(byte))
            continue
        custom = True
        char = custom_map.get(byte)
        if char is None:
            unknown.append(f"{byte:02X}")
            out.append(decode_cp932(bytes([byte]), "Name", index))
        else:
            out.append(char)
    text = "".join(out).strip()
    if unknown:
        return f"{text} / {original_name}", "partial-custom-fallback"
    if custom:
        return text, "custom-korean"
    return text or original_name, "ascii-patched"


def main() -> None:
    original = executable(ORIGINAL_DISC)
    patched = executable(PATCHED_DISC)
    custom_map = derive_custom_map(patched)

    characters: list[str] = []
    report: list[dict[str, object]] = []
    for index in range(CHARACTER_COUNT):
        original_raw = raw_entry(original, CHARACTER_TABLE, index, CHARACTER_WIDTH)
        patched_raw = raw_entry(patched, CHARACTER_TABLE, index, CHARACTER_WIDTH)
        original_name = decode_cp932(original_raw, "Name", index)
        name, source = decode_patched_name(patched_raw, original_name, custom_map, index)
        characters.append(name)
        report.append(
            {
                "index": index,
                "original_hex": original_raw.hex().upper(),
                "patched_hex": patched_raw.hex().upper(),
                "original_name": original_name,
                "editor_name": name,
                "source": source,
            }
        )

    UI.mkdir(parents=True, exist_ok=True)
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    (UI / "character_names.json").write_text(
        json.dumps(characters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ANALYSIS / "korean-name-extraction.json").write_text(
        json.dumps(
            {
                "character_count": len(characters),
                "class_count": CLASS_COUNT,
                "custom_byte_map": {f"{k:02X}": v for k, v in sorted(custom_map.items())},
                "sources": {
                    "original_disc": str(ORIGINAL_DISC.relative_to(ROOT)),
                    "patched_disc": str(PATCHED_DISC.relative_to(ROOT)),
                },
                "records": report,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for item in report:
        counts[str(item["source"])] = counts.get(str(item["source"]), 0) + 1
    print(
        json.dumps(
            {
                "generated_characters": len(characters),
                "expected_classes": CLASS_COUNT,
                "custom_map_entries": len(custom_map),
                "source_counts": counts,
                "trislen": characters[265],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
