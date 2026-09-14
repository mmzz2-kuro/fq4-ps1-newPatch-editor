# FQ4-PLAN-029 CLASS 213~218 4x4 아이콘 반영
- 작성일: 2026-09-14
- 상태: **완료**
- 대상 도구: `tools/FQ4SaveEditor/`
- 관련 스크립트: `tools/scripts/extract_fq4_class_icons.py`
- 완료 문서 예정: `docs/fq4/finish/029-save-editor-4x4-class-icons-213-218.md`

## 1. 문제

CLASS 213~218도 기존 2x2 또는 3x3 규칙으로는 아이콘이 일부만 보인다. 사용자 확인에 따라 이 구간도 211~212와 같은 4x4 `base_tile=64` 규칙을 적용해야 한다.

## 2. 목표

- CLASS 213~218에 4x4 `base_tile=64` 프레임 규칙을 적용한다.
- 기존 CLASS 211~212의 4x4 규칙을 유지한다.
- 기존 2x2와 3x3 규칙은 변경하지 않는다.
- 색상은 이번 작업에서 조정하지 않는다.

## 3. 구현 방향

- `extract_fq4_class_icons.py`의 4x4 특별 처리 범위를 211~218로 확장한다.
- `class_catalog.json`에 213~218도 `width_tiles=4`, `height_tiles=4`, `base_tile=64`, `column_major=true`로 기록한다.
- 확인용 이미지를 `docs/fq4/analysis/029/`에 생성한다.

## 4. 검증

- CLASS 211~218이 모두 4x4 base 64로 표시되는지 확인한다.
- CLASS 25의 2x2 규칙이 유지되는지 확인한다.
- CLASS 174/183의 3x3 규칙이 유지되는지 확인한다.
- 세이브 에디터 EXE를 다시 빌드한다.

## 5. 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 하며 수정하지 않는다.

## 6. 완료 조건

- CLASS 213~218 아이콘이 4x4 base 64로 반영된다.
- 확인용 이미지와 완료 문서가 작성된다.
