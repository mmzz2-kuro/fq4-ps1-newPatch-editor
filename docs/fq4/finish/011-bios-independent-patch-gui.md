# FQ4-FINISH-011 일반 BIOS용 한글 ROM 생성 GUI

- 완료일: 2026-09-13
- 결과: **완료**
- 계획: [PLAN-011](../plans/011-bios-independent-patch-gui.md)
- 분석: [analysis/011](../analysis/011/README.md)

## 완성된 도구

- `tools/fq4_bios_independent_gui.py`: tkinter 사용자 GUI
- `tools/scripts/build_fq4_bios_independent.py`: 경로 인자 기반 변환 엔진
- `tools/scripts/verify_fq4_gui_output.py`: 결과 BIN/CUE 검증기
- `tools/README-fq4-gui.md`: 사용자 설명서

GUI는 일본판 원본 BIN, 250826 한글패치, 한글 BIOS와 출력 위치를 받아 일반 BIOS용 BIN/CUE를 생성한다. 해시가 다른 원본·패치·BIOS는 쓰기 전에 거부한다.

## 검증 결과

- PLAN-010 ROM과 byte 단위 재현: 통과
- 결과 SHA-256: `95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e`
- 결과 크기: 101,140,704바이트
- 한글·공백 경로: 통과
- UTF-8 CUE와 `MODE2/2352`: 통과
- 241112 패치 사전 차단: 통과
- 기존 출력 덮어쓰기 보호: 통과
- 실패 후 임시 BIN 제거: 통과
- Python 문법 및 tkinter 8.6: 통과

GUI 시험용 전체 ROM은 검증 후 삭제했다. 프로젝트에는 기존 `work/fq4/rom/current.bin` 한 벌만 남아 있으며 `original/`, `patched/`, `korean-patch/`의 입력은 수정하지 않았다.

## 실행 방법

```text
python tools/fq4_bios_independent_gui.py
```

현재 단계는 Python GUI까지 완료했다. Python 설치 없이 실행하는 단일 Windows EXE는 후속 계획에서 만들 수 있다.
