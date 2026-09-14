# FQ4-FINISH-030 CLASS 217~218 대형 예외 아이콘 반영
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/030-save-editor-class-217-218-large-exceptions.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

CLASS 217, 218을 사용자 확정값에 따라 대형 예외 프레임으로 반영했다.

적용 규칙:

```text
217: base_tile=0, 6x6, column-major
218: base_tile=0, 8x8, column-major
```

211~216의 4x4 base 64 규칙, 기존 2x2 규칙, 기존 3x3 규칙은 유지했다.

## 구현

`tools/scripts/extract_fq4_class_icons.py`의 `layout()`에 217, 218 전용 분기를 추가했다.

큰 프레임은 64x64 아이콘 영역에 맞춰 비율 유지 축소 후 중앙 배치한다. 색상은 이번 작업에서 조정하지 않았다.

## 확인

확인용 이미지:

- `docs/fq4/analysis/030/class-217-218-exception-check.png`
- `docs/fq4/analysis/030/class-217-larger-frame-candidates.png`
- `docs/fq4/analysis/030/class-218-larger-frame-candidates.png`

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 217: 6x6 base 0 column-major 기록 확인
- CLASS 218: 8x8 base 0 column-major 기록 확인
- CLASS 25, 174, 211, 216 규칙 유지 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`4EAE6AD2950B499DD23CC76C845285DA5D64F878757A64881464491F55461D00`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
