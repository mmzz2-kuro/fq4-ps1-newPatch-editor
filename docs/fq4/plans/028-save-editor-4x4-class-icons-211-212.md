# FQ4-PLAN-028 CLASS 211~212 4x4 아이콘 반영
- 작성일: 2026-09-14
- 상태: **완료**
- 대상 도구: `tools/FQ4SaveEditor/`
- 관련 스크립트: `tools/scripts/extract_fq4_class_icons.py`
- 완료 문서 예정: `docs/fq4/finish/028-save-editor-4x4-class-icons-211-212.md`

## 1. 문제

CLASS 211, 212는 192타일 리소스이며 기존 2x2 또는 3x3 프레임 규칙으로는 온전한 아이콘이 나오지 않는다.

확인용 이미지에서 사용자가 `4x4 base 64`가 제대로 보인다고 확인했다.

## 2. 목표

- CLASS 211과 212에만 4x4 프레임 규칙을 적용한다.
- 적용 프레임은 `base_tile=64`, 4x4타일, 세로열 우선 조합으로 한다.
- 기존 2x2, 3x3 아이콘 규칙은 유지한다.
- 색상은 이번 작업에서 조정하지 않는다.

## 3. 구현 방향

- `extract_fq4_class_icons.py`의 `layout()`에서 class id 211, 212를 특별 처리한다.
- 4x4 프레임은 64x64 원본 크기이므로 crop/resize 없이 64x64 캔버스에 그대로 사용한다.
- `class_catalog.json`에는 `width_tiles=4`, `height_tiles=4`, `base_tile=64`, `column_major=true`로 기록한다.

## 4. 검증

- CLASS 211, 212가 4x4 base 64로 표시되는지 확인한다.
- CLASS 25의 2x2 타일 순서가 유지되는지 확인한다.
- CLASS 174/183 이후 3x3 타일 순서가 유지되는지 확인한다.
- 세이브 에디터 EXE를 다시 빌드한다.

## 5. 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 하며 수정하지 않는다.

## 6. 완료 조건

- CLASS 211, 212 아이콘이 4x4 base 64로 반영된다.
- 확인용 이미지와 완료 문서가 작성된다.
