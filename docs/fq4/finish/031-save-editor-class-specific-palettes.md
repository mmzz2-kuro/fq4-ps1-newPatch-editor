# FQ4-FINISH-031 세이브 에디터 CLASS별 팔레트 적용
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/031-save-editor-class-specific-palettes.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

CLASS 000 `왕 아레스(변신전)`과 CLASS 010 `엑소시스트(슈이키)`에 class별 팔레트 override를 적용했다.

전역 팔레트는 유지하고, 두 샘플 항목만 `class_specific_sample_override_v1`로 기록했다. 기존 2x2, 3x3, 4x4, 6x6, 8x8 타일 레이아웃 규칙은 변경하지 않았다.

## 적용 색상 방향

CLASS 000:

- 검정/짙은 회색 머리
- 피부색 얼굴
- 흰색/하늘색 갑옷
- 갈색 부츠
- 흰색/회색 검 계열

CLASS 010:

- 검정 머리
- 노랑 머리 장식
- 피부색 얼굴과 팔
- 초록 의상
- 주황 하의/신발
- 갈색 지팡이

## 분석 산출물

- `docs/fq4/analysis/031/class-000-index-map.png`
- `docs/fq4/analysis/031/class-010-index-map.png`
- `docs/fq4/analysis/031/class-specific-palette-check.png`

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 000/010: `class_specific_sample_override_v1` 기록 확인
- CLASS 25, 217, 218의 기존 레이아웃 규칙 유지 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`C128940A5DF5B37F5EEEBA8E10AEA488EB5102D6AF8AF6172ACB2385C447D4C8`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
