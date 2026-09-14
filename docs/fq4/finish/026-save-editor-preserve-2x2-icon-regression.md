# FQ4-FINISH-026 기존 2x2 CLASS 아이콘 규격 복구
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/026-save-editor-preserve-2x2-icon-regression.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

PLAN-025의 대형 3x3 보정 과정에서 기존 2x2 아이콘까지 자동 crop/center fit이 적용되던 회귀를 복구했다.

현재 출력 규칙은 다음과 같다.

- 2x2 리소스: crop 없이 32x32 프레임을 64x64로 단순 2배 확대
- compact 2x2 리소스: crop 없이 64x64 단순 확대
- 대형 3x3 리소스: 세로열 우선 조합을 유지하고 64x64 캔버스 중앙에 배치

따라서 CLASS 25 같은 기존 정상 아이콘은 이전 규격으로 돌아가고, CLASS 174/183 이후 대형 아이콘 보정은 유지된다.

## 수정

`tools/scripts/extract_fq4_class_icons.py`에서 `fit_large_icon()`을 대형 3x3 전용으로 분리했다.

2x2 경로는 다음 처리만 수행한다.

```text
32x32 -> 64x64 NEAREST resize
```

3x3 경로는 다음 처리를 유지한다.

```text
48x48 column-major frame -> transparent 64x64 centered canvas
```

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 25: 2x2, `column_major=false` 확인
- CLASS 174/183/199/203: 3x3, `column_major=true` 확인
- `docs/fq4/analysis/026/icon-regression-check.png` 생성 및 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`879F3567CF2604242B3B18DB7EEA13C79A0E0D86FBAE3AF19AB5E3203D5F668A`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
