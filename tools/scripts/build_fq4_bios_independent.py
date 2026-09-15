#!/usr/bin/env python3
"""Build the verified FQ4 Korean ROM for a standard PS1 BIOS."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/scripts"))
from build_bios_independent_poc import BIOS_SHA, ORIGINAL_SHA  # noqa: E402
import build_full_font_runtime as runtime  # noqa: E402
from build_party_race_limit_patch import apply_species_budget_expansion  # noqa: E402
from fq4_patch_profile import detect, validate_sector_envelope  # noqa: E402
from repair_cdrom_xa_ecc import repair_image  # noqa: E402
from verify_cdrom_xa_ecc import audit_range  # noqa: E402

EXPECTED_SIZE = 101_140_704

RAW_SECTOR = 2352
FORM1_DATA_OFFSET = 24
FORM1_DATA_SIZE = 2048
ENDING_MOV04_LBA_START = 18430
ENDING_MOV04_LBA_END = 22652
ENDING_TEMPLATE_EXE_OFFSET = 0xE0400
ENDING_TEMPLATE_LENGTH = 0xB0
ENDING_TEMPLATE_REPLACEMENTS = (
    ("名前", bytes.fromhex("90 ca 8c a5"), "이름"),
    ("クラス", bytes.fromhex("91 97 8f f5 20 20"), "직업"),
    ("パワー", bytes.fromhex("93 c2 90 96 20 20"), "파워"),
    ("討数", bytes.fromhex("88 db 92 7e"), "격추"),
    ("戦場より生還！", bytes.fromhex("90 fa 90 e3 90 40 8e ab 8e 9d 94 ad 81 49"), "전장에서생환!"),
    ("にて死亡", bytes.fromhex("90 40 8e ab 8e 87 8c bf"), "에서사망"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def emit(stage: str, message: str, **extra: object) -> None:
    line = json.dumps({"stage": stage, "message": message, **extra}, ensure_ascii=False) + "\n"
    encoded = line.encode("utf-8")
    try:
        os.write(sys.stdout.fileno(), encoded)
    except (AttributeError, OSError, ValueError):
        print(line, end="", flush=True)


def cue_text(bin_name: str) -> str:
    return f'FILE "{bin_name}" BINARY\r\n  TRACK 01 MODE2/2352\r\n    INDEX 01 00:00:00\r\n'



def read_form1_file(image: bytes, lba: int, size: int) -> bytes:
    sectors = (size + FORM1_DATA_SIZE - 1) // FORM1_DATA_SIZE
    return b"".join(
        image[(lba + i) * RAW_SECTOR + FORM1_DATA_OFFSET:(lba + i) * RAW_SECTOR + FORM1_DATA_OFFSET + FORM1_DATA_SIZE]
        for i in range(sectors)
    )[:size]


def write_form1_file_slice(image: bytearray, lba0: int, logical_offset: int, payload: bytes) -> list[int]:
    touched: set[int] = set()
    position = 0
    while position < len(payload):
        logical = logical_offset + position
        lba = lba0 + logical // FORM1_DATA_SIZE
        in_sector = logical % FORM1_DATA_SIZE
        length = min(len(payload) - position, FORM1_DATA_SIZE - in_sector)
        start = lba * RAW_SECTOR + FORM1_DATA_OFFSET + in_sector
        image[start:start + length] = payload[position:position + length]
        touched.add(lba)
        position += length
    return sorted(touched)


def apply_ending_result_fix(image: bytearray, original_image: bytes, exe_lba: int, exe_size: int) -> dict[str, object]:
    for lba in range(ENDING_MOV04_LBA_START, ENDING_MOV04_LBA_END + 1):
        start = lba * RAW_SECTOR
        image[start:start + RAW_SECTOR] = original_image[start:start + RAW_SECTOR]

    original_exe = read_form1_file(original_image, exe_lba, exe_size)
    template = bytearray(original_exe[ENDING_TEMPLATE_EXE_OFFSET:ENDING_TEMPLATE_EXE_OFFSET + ENDING_TEMPLATE_LENGTH])
    replacements = []
    for old_text, new, new_text in ENDING_TEMPLATE_REPLACEMENTS:
        old = old_text.encode("cp932")
        rel = bytes(template).find(old)
        if rel < 0:
            raise ValueError(f"엔딩 결산 원본 라벨을 찾을 수 없습니다: {old_text}")
        if len(new) > len(old):
            raise ValueError(f"엔딩 결산 라벨이 원본 폭을 초과합니다: {new_text} {len(new)}>{len(old)}")
        template[rel:rel + len(old)] = new + b" " * (len(old) - len(new))
        replacements.append({
            "relative_offset": hex(rel),
            "old_text": old_text,
            "new_text": new_text,
            "old_bytes": old.hex(" "),
            "new_game_bytes_padded": bytes(template[rel:rel + len(old)]).hex(" "),
        })
    touched_template = write_form1_file_slice(image, exe_lba, ENDING_TEMPLATE_EXE_OFFSET, bytes(template))
    return {
        "mov04_replaced_lba": [ENDING_MOV04_LBA_START, ENDING_MOV04_LBA_END],
        "template_offset": hex(ENDING_TEMPLATE_EXE_OFFSET),
        "template_length": hex(ENDING_TEMPLATE_LENGTH),
        "template_touched_lba": touched_template,
        "replacements": replacements,
    }


def build(original: Path, patch: Path, bios: Path, output: Path, xdelta: Path, overwrite: bool,
          expand_party_species_limit: bool = False, fix_ending_result: bool = False) -> dict[str, object]:
    paths = [item.resolve() for item in (original, patch, bios, output, xdelta)]
    original, patch, bios, output, xdelta = paths
    if len({str(original).casefold(), str(patch).casefold(), str(bios).casefold(), str(output).casefold()}) != 4:
        raise ValueError("출력 BIN은 입력 파일과 다른 경로여야 합니다.")
    for label, path in (("원본 BIN", original), ("한글패치", patch), ("한글 BIOS", bios), ("xdelta", xdelta)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} 파일을 찾을 수 없습니다: {path}")
    output.parent.mkdir(parents=True, exist_ok=True)
    cue = output.with_suffix(".cue")
    if (output.exists() or cue.exists()) and not overwrite:
        raise FileExistsError("출력 BIN 또는 CUE가 이미 있습니다. --overwrite가 필요합니다.")
    temp = output.with_name(f".{output.name}.fq4-building.bin")
    temp_cue = cue.with_name(f".{cue.name}.fq4-building.cue")
    if temp.exists():
        temp.unlink()
    if temp_cue.exists():
        temp_cue.unlink()
    try:
        emit("input", "입력 파일을 검사하고 있습니다.")
        identities = {"original": sha256(original), "patch": sha256(patch), "bios": sha256(bios)}
        expected = {"original": ORIGINAL_SHA, "bios": BIOS_SHA}
        failures = [name for name in expected if identities[name] != expected[name]]
        if failures:
            raise ValueError("지원하지 않는 입력: " + ", ".join(failures))

        emit("korean_patch", "선택한 한글패치 xdelta를 적용하고 있습니다.")
        result = subprocess.run([str(xdelta), "-d", "-f", "-s", str(original), str(patch), str(temp)], capture_output=True, text=True)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"xdelta 적용 실패({result.returncode}): {detail}")
        structure = detect(temp)
        sector_structure = validate_sector_envelope(temp)
        emit("profile", "호환 구조를 확인했습니다.", patch_sha256=identities["patch"], **structure)

        emit("bios_independent", "일반 BIOS용 글꼴과 로더를 적용하고 있습니다.")
        report_dir = output.parent / f".{output.stem}.fq4-report"
        runtime.ROM = temp
        runtime.BIOS = bios
        runtime.OUT = report_dir
        runtime.START_SHA = structure["image_sha256"]
        runtime.EXE_LBA = structure["exe_lba"]
        runtime.EXE_SIZE = structure["exe_size"]
        runtime.DUMMY_LBA = structure["dummy_lba"]
        runtime.INIT_CALL = structure["init_call"]
        runtime.KROM_HOOK = structure["krom_hook"]
        # The development builder prints a detailed manifest summary. Keep the
        # product protocol to one compact JSON event per user-visible stage.
        with contextlib.redirect_stdout(io.StringIO()):
            runtime.main()

        species_report = None
        if expand_party_species_limit:
            emit("species_limit", "부대 종족 제한 확장을 적용하고 있습니다.")
            image = bytearray(temp.read_bytes())
            species_report = apply_species_budget_expansion(image)
            temp.write_bytes(image)

        ending_report = None
        if fix_ending_result:
            emit("ending_fix", "엔딩 동영상 이후 결산 화면 수정을 적용하고 있습니다.")
            image = bytearray(temp.read_bytes())
            ending_report = apply_ending_result_fix(image, original.read_bytes(), structure["exe_lba"], structure["exe_size"])
            temp.write_bytes(image)


        emit("ecc_repair", "전체 디스크의 EDC/ECC를 검사하고 교정하고 있습니다.")
        repair = repair_image(temp, workers=1)

        emit("verify", "완성된 디스크를 검증하고 있습니다.")
        output_sha = sha256(temp)
        if temp.stat().st_size != EXPECTED_SIZE:
            raise ValueError("완성 ROM 크기가 원본 디스크와 다릅니다.")
        audit = audit_range((str(temp), 0, temp.stat().st_size // 2352))
        failure_counts = {name: len(values) for name, values in audit["failures"].items()}
        if any(failure_counts.values()):
            raise ValueError(f"최종 EDC/ECC 검증 실패: {failure_counts}")
        manifest = json.loads((report_dir / "build-manifest.json").read_text(encoding="utf-8"))
        if not manifest["raw_diff_sectors"]:
            raise ValueError("일반 BIOS용 로더 변경 sector가 기록되지 않았습니다.")
        # UTF-8 BOM keeps ASCII-only CUEs compatible while allowing Korean and
        # other Unicode BIN filenames on Windows/DuckStation.
        temp_cue.write_text(cue_text(output.name), encoding="utf-8-sig", newline="")
        os.replace(temp, output)
        os.replace(temp_cue, cue)
        for item in report_dir.glob("*"):
            item.unlink()
        report_dir.rmdir()
        final = {"status": "success", "output": str(output), "cue": str(cue), "size": output.stat().st_size, "sha256": output_sha, "patch_sha256": identities["patch"], "profile": structure["profile"], "structure": structure, "sector_structure": sector_structure, "final_failure_counts": failure_counts, "repaired_sectors": repair["repaired_sector_count"], "party_species_limit_expanded": expand_party_species_limit}
        if species_report is not None:
            final["species_limit_touched_sectors"] = species_report["touched_sectors"]
        if ending_report is not None:
            final["ending_result_fix"] = ending_report
        emit("complete", "일반 BIOS용 ROM 생성이 완료되었습니다.", **final)
        return final
    except BaseException:
        for path in (temp, temp_cue):
            if path.exists():
                path.unlink()
        report_dir = output.parent / f".{output.stem}.fq4-report"
        if report_dir.exists():
            for item in report_dir.glob("*"):
                item.unlink()
            report_dir.rmdir()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--bios", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xdelta-exe", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--expand-party-species-limit", action="store_true")
    parser.add_argument("--fix-ending-result", action="store_true")
    args = parser.parse_args()
    try:
        build(args.original, args.patch, args.bios, args.output, args.xdelta_exe, args.overwrite,
              args.expand_party_species_limit, args.fix_ending_result)
    except Exception as exc:
        emit("error", str(exc), error_type=type(exc).__name__)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
