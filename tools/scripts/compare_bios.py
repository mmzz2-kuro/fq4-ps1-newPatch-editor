#!/usr/bin/env python3
"""Record hashes and byte-difference bounds for the normal and supplied FQ4 BIOSes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NORMAL = ROOT / "original" / "scph1001.bin"
SUPPLIED = ROOT / "korean-patch" / "SCPH1001.BIN"
OUTPUT = ROOT / "docs" / "fq4" / "analysis" / "002" / "bios-comparison.json"


def hashes(data: bytes) -> dict[str, str]:
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),  # noqa: S324 - file identity only
    }


def main() -> None:
    normal = NORMAL.read_bytes()
    supplied = SUPPLIED.read_bytes()
    if len(normal) != len(supplied):
        raise SystemExit("BIOS sizes differ; bytewise comparison is not valid")

    offsets = [i for i, (left, right) in enumerate(zip(normal, supplied)) if left != right]
    if not offsets:
        raise SystemExit("BIOS files are identical")

    first, last = offsets[0], offsets[-1]
    version_marker = b"System ROM Version"
    # The BIOS contains older embedded version strings; the final marker is the
    # build identity printed by the ROM itself.
    version_offset = normal.rfind(version_marker)
    version_text = (
        normal[version_offset : version_offset + 64]
        .split(b"\x00", 1)[0]
        .decode("ascii")
        .strip()
        if version_offset >= 0
        else None
    )

    result = {
        "purpose": "Supplementary input record added after the immutable initial ROM survey",
        "normal_bios": {"path": NORMAL.relative_to(ROOT).as_posix(), **hashes(normal)},
        "supplied_korean_bios": {
            "path": SUPPLIED.relative_to(ROOT).as_posix(),
            **hashes(supplied),
        },
        "comparison": {
            "same_size": True,
            "different_byte_count": len(offsets),
            "first_difference": f"0x{first:x}",
            "last_difference": f"0x{last:x}",
            "differences_outside_reported_bounds": False,
            "identical_before_first_difference": normal[:first] == supplied[:first],
            "identical_after_last_difference": normal[last + 1 :] == supplied[last + 1 :],
        },
        "rom_version_text": version_text,
        "rom_version_text_matches": version_text is not None
        and version_text.encode("ascii") in supplied,
        "interpretation_limit": (
            "The bounded difference region is consistent with a glyph-data replacement, "
            "but byte comparison alone does not prove the semantic role of every changed byte."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
