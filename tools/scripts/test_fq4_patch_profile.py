#!/usr/bin/env python3
"""Small regression fixtures for the version-independent FQ4 patch profile."""
from __future__ import annotations

import json
from pathlib import Path

from fq4_patch_profile import INIT_ANCHOR, unique

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    profiles = []
    for version in ("241112", "250826"):
        path = ROOT / "docs" / "fq4" / "analysis" / "014" / f"profile-{version}.json"
        profile = json.loads(path.read_text(encoding="utf-8"))
        assert profile["profile"] == "fq4-korean-sjis-v1"
        assert profile["exe_lba"] == 24 and profile["dummy_lba"] == 24184
        assert profile["init_call"] == 0x80013A38 and profile["krom_hook"] == 0x80082C8C
        profiles.append(profile)
    assert profiles[0]["image_sha256"] != profiles[1]["image_sha256"]
    assert unique(b"prefix" + INIT_ANCHOR + b"suffix", INIT_ANCHOR, "fixture") == 6
    for fixture in (b"missing", INIT_ANCHOR + INIT_ANCHOR):
        try:
            unique(fixture, INIT_ANCHOR, "fixture")
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe signature fixture was accepted")
    print("PASS: 241112/250826 common profile and missing/duplicate signature rejection")


if __name__ == "__main__":
    main()
