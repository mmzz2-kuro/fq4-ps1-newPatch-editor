#!/usr/bin/env python3
"""Verify an FQ4 GUI product BIN/CUE without modifying it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA = "616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d"
EXPECTED_SIZE = 101_140_704


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bin", type=Path)
    args = parser.parse_args()
    image = args.bin.resolve()
    cue = image.with_suffix(".cue")
    expected_cue = f'FILE "{image.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
    actual_sha = sha256(image)
    cue_text = cue.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    result = {
        "pass": image.stat().st_size == EXPECTED_SIZE and actual_sha == EXPECTED_SHA and cue_text == expected_cue,
        "bin": str(image), "cue": str(cue), "size": image.stat().st_size,
        "sha256": actual_sha, "cue_valid": cue_text == expected_cue,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
