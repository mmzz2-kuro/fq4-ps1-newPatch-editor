# FQ4-PLAN-026 기존 2x2 CLASS 아이콘 규격 복구
- 작성일: 2026-09-14
- 상태: **완료**
- 대상 도구: `tools/FQ4SaveEditor/`
- 관련 스크립트: `tools/scripts/extract_fq4_class_icons.py`
- 완료 문서 예정: `docs/fq4/finish/026-save-editor-preserve-2x2-icon-regression.md`

## 1. 문제

PLAN-025에서 대형 3x3 스프라이트의 타일 순서를 고치면서 모든 아이콘 출력에 자동 crop/fit을 적용했다. 이 때문에 기존에 정상적으로 보이던 2x2 CLASS 아이콘도 위치와 여백 규격이 바뀌었다.

사용자가 지적한 문제는 대형 3x3 항목만 보정하면 되는데, 정상 2x2 항목까지 출력 규격이 달라진 것이다.

## 2. 목표

- 기존 2x2 아이콘은 PLAN-018/021 당시처럼 32x32 프레임을 64x64로 단순 2배 확대한다.
- 대형 3x3 아이콘만 48x48 프레임을 64x64 캔버스 중앙에 맞춘다.
- compact 2x2 리소스도 기존처럼 64x64 단순 확대를 유지한다.
- CLASS 25 같은 이미 승인된 정상 항목의 위치감과 크기를 복구한다.

## 3. 구현 방향

- `extract_fq4_class_icons.py`의 `fit_icon()`을 대형 3x3 전용으로 제한한다.
- 2x2 리소스는 crop 없이 `resize((64,64), NEAREST)`만 수행한다.
- catalog에는 2x2와 3x3 처리 방식을 구분해 기록한다.

## 4. 검증

- CLASS 25가 기존 64x64 단순 확대 규격으로 돌아왔는지 확인한다.
- CLASS 174/183 이후 3x3 항목은 세로열 우선 조합이 유지되는지 확인한다.
- `class_catalog.json` 220개 항목을 유지한다.
- 세이브 에디터 EXE를 다시 빌드한다.

## 5. 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 하며 수정하지 않는다.

## 6. 완료 조건

- 2x2 아이콘 규격 회귀가 복구된다.
- 3x3 대형 보정은 유지된다.
- 완료 문서가 작성된다.
