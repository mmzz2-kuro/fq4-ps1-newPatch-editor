# FQ4-PLAN-030 CLASS 217~218 대형 예외 아이콘 반영
- 작성일: 2026-09-14
- 상태: **완료**
- 대상 도구: `tools/FQ4SaveEditor/`
- 관련 스크립트: `tools/scripts/extract_fq4_class_icons.py`
- 완료 문서 예정: `docs/fq4/finish/030-save-editor-class-217-218-large-exceptions.md`

## 1. 문제

CLASS 217, 218은 211~216과 같은 4x4 base 64 규칙으로 처리하면 조각처럼 보인다. 추가 후보 이미지에서 두 항목은 서로 다른 대형 예외 구조로 확인됐다.

사용자 확정값:

- CLASS 217: 6x6, base 0
- CLASS 218: 8x8, base 0

## 2. 목표

- CLASS 217을 6x6 base 0으로 예외 처리한다.
- CLASS 218을 8x8 base 0으로 예외 처리한다.
- CLASS 211~216의 4x4 base 64 규칙은 유지한다.
- 기존 2x2, 3x3 규칙도 유지한다.
- 색상은 이번 작업에서 조정하지 않는다.

## 3. 구현 방향

- `extract_fq4_class_icons.py`의 `layout()`에 217, 218 전용 분기를 추가한다.
- 217은 `base_tile=0`, `width_tiles=6`, `height_tiles=6`, `column_major=true`로 기록한다.
- 218은 `base_tile=0`, `width_tiles=8`, `height_tiles=8`, `column_major=true`로 기록한다.
- GUI 목록용 PNG는 기존 64x64 영역에 맞춰 축소/중앙 배치한다.

## 4. 검증

- CLASS 217, 218이 각각 확정한 큰 프레임으로 표시되는지 확인한다.
- CLASS 211~216 4x4 규칙이 유지되는지 확인한다.
- CLASS 25 2x2, CLASS 174/183 3x3 규칙이 유지되는지 확인한다.
- 세이브 에디터 EXE를 다시 빌드한다.

## 5. 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 하며 수정하지 않는다.

## 6. 완료 조건

- CLASS 217, 218 대형 예외 아이콘이 반영된다.
- 확인용 이미지와 완료 문서가 작성된다.
