#!/usr/bin/env python3
"""Write the reproducible evidence record for FQ4 PLAN-003."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BIOS = ROOT / "original" / "scph1001.bin"
WORK_BIOS = ROOT / "work" / "fq4" / "tools" / "duckstation" / "bios" / "scph1001.bin"
ROM = ROOT / "work" / "fq4" / "rom" / "current.bin"
CUE = ROOT / "work" / "fq4" / "rom" / "current.cue"
LOG = ROOT / "work" / "fq4" / "tools" / "duckstation" / "duckstation.log"
EVIDENCE_DIR = ROOT / "docs" / "fq4" / "analysis" / "003"
WORK_DIR = ROOT / "work" / "fq4" / "003"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    log_text = LOG.read_text(encoding="utf-8", errors="replace")
    rom_bins = sorted((ROOT / "work" / "fq4" / "rom").glob("*.bin"))
    record = {
        "plan": "FQ4-PLAN-003",
        "result": "unresolved",
        "inputs": {
            "normal_bios": {"path": BIOS.relative_to(ROOT).as_posix(), "sha256": sha256(BIOS)},
            "duckstation_bios_copy": {"path": WORK_BIOS.relative_to(ROOT).as_posix(), "sha256": sha256(WORK_BIOS)},
            "work_rom": {"path": ROM.relative_to(ROOT).as_posix(), "size": ROM.stat().st_size, "sha256": sha256(ROM)},
            "cue": {"path": CUE.relative_to(ROOT).as_posix(), "sha256": sha256(CUE)},
        },
        "boot_observation": {
            "game_id_slps_00604": "SLPS-00604" in log_text,
            "bios_v2_2_selected": "(v2.2 12-04-95 A)" in log_text,
            "bios_region_ntsc_u": "BIOS Region: NTSC-U" in log_text,
            "disc_region_ntsc_j": "disc region: NTSC-J" in log_text,
            "system_booted": "System booted" in log_text,
            "kernel_initialized": "Kernel initialized" in log_text,
        },
        "visual_observation": {
            "representative_screen_reached_by_normal_input": False,
            "final_pixels_observed": False,
            "exit_and_reentry_tested": False,
            "screenshots_created": 0,
        },
        "automation_failures": [
            "Trusted RPC service is not configured: sky",
            "cua.listApps is not a function",
            "Windows sandbox failed while applying deny-read ACLs; node_repl kernel exited",
        ],
        "single_work_rom": {
            "bin_count": len(rom_bins),
            "paths": [path.relative_to(ROOT).as_posix() for path in rom_bins],
            "pass": rom_bins == [ROM],
        },
        "claim_limit": "This run proves a fresh normal-BIOS boot only. It does not prove normal-input reachability, final Korean pixels, surrounding UI integrity, or exit/re-entry behavior.",
    }
    if not all(record["boot_observation"].values()):
        raise SystemExit("DuckStation log does not contain every expected boot marker")
    if record["inputs"]["normal_bios"]["sha256"] != record["inputs"]["duckstation_bios_copy"]["sha256"]:
        raise SystemExit("DuckStation BIOS copy differs from the preserved normal BIOS")
    if not record["single_work_rom"]["pass"]:
        raise SystemExit("More than one work ROM BIN exists")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "runtime-visual-verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(LOG, WORK_DIR / "duckstation.log")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
