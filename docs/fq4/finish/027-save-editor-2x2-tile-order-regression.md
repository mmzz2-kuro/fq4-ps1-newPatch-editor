# FQ4-FINISH-027 기존 2x2 CLASS 타일 순서 복구
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/027-save-editor-2x2-tile-order-regression.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

2x2 CLASS 아이콘의 타일 순서 회귀를 복구했다.

사용자 확인 기준:

```text
16 = 좌상
17 = 좌하
18 = 우상
19 = 우하
```

따라서 화면 배치는 다음과 같다.

```text
16 18
17 19
```

`tools/scripts/extract_fq4_class_icons.py`에서 2x2도 세로열 우선 조합을 사용하도록 수정했다. 3x3 대형 리소스의 세로열 우선 조합도 그대로 유지했다.

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 25와 27: 2x2, `column_major=true` 확인
- CLASS 174, 183, 203: 3x3, `column_major=true` 확인
- `docs/fq4/analysis/027/tile-order-regression-check.png` 생성 및 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`A913B74A567A25C30277DA75CAF202A9F8CA8406D04F478C10397EE0EC649C79`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
