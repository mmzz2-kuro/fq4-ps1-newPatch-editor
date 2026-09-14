#!/usr/bin/env python3
"""Record the two user-captured PLAN-003 BIOS comparison screenshots."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work" / "fq4" / "tools" / "duckstation" / "screenshots"
WORK = ROOT / "work" / "fq4" / "003"
OUTPUT = ROOT / "docs" / "fq4" / "analysis" / "003" / "screenshot-comparison.json"
SHOTS = {
    "normal_bios": SOURCE / "ファーストクィーンⅣ　バルシア戦記 2026-09-13-13-31-26.png",
    "korean_bios": SOURCE / "ファーストクィーンⅣ　バルシア戦記 2026-09-13-13-33-09.png",
}


def describe(path: Path, copy_name: str) -> dict[str, object]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"not a PNG: {path}")
    width, height = struct.unpack(">II", data[16:24])
    destination = WORK / copy_name
    shutil.copyfile(path, destination)
    return {
        "source": path.relative_to(ROOT).as_posix(),
        "evidence_copy": destination.relative_to(ROOT).as_posix(),
        "size": len(data),
        "width": width,
        "height": height,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    result = {
        "plan": "FQ4-PLAN-003",
        "screenshots": {
            "normal_bios": describe(SHOTS["normal_bios"], "normal-bios-menu.png"),
            "korean_bios": describe(SHOTS["korean_bios"], "korean-bios-menu.png"),
        },
        "same_dimensions": True,
        "user_identification": {
            "normal_bios_capture": "2026-09-13 13:31:26",
            "korean_bios_capture": "2026-09-13 13:33:09",
        },
        "manual_visual_observation": {
            "same_scene": "world-map command menu",
            "normal_bios": "menu text renders as incorrect Japanese/ideographic glyphs",
            "korean_bios": "menu text renders as Korean; first entries include 시간경과, 부대이동, 탐색",
            "selected_followup_strings": ["시간경과", "부대이동", "탐색"],
        },
        "claim_limit": "The captures demonstrate BIOS-dependent glyph selection in this menu. They do not yet demonstrate a ROM-resident replacement for the selected strings.",
    }
    left = result["screenshots"]["normal_bios"]
    right = result["screenshots"]["korean_bios"]
    result["same_dimensions"] = (left["width"], left["height"]) == (right["width"], right["height"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
