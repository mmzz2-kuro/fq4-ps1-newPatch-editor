# FQ4-PLAN-032 CLASS 인덱스 지도 랜덤 샘플 생성
- 작성일: 2026-09-14
- 상태: **보류**
- 대상 스크립트: `tools/scripts/`
- 출력 예정: `docs/fq4/analysis/032/`
- 완료 문서 예정: `docs/fq4/finish/032-class-index-map-random-samples.md`

## 1. 목적

CLASS별 팔레트 보정을 쉽게 하기 위해 `class-000-index-map.png`처럼 스프라이트 픽셀의 팔레트 인덱스 번호가 표시된 이미지를 만든다.

이번에는 전체 CLASS 중 대략 10개를 랜덤하게 뽑되, 서로 사용하는 팔레트 인덱스가 되도록 많이 겹치지 않게 선택한다.

## 2. 범위

- CLASS 아이콘 추출에 사용하는 현재 대표 프레임 기준으로 인덱스 지도를 만든다.
- 각 픽셀 블록에는 원본 스프라이트 픽셀 인덱스 값을 표시한다.
- 이미지별로 사용된 인덱스 목록과 선택 근거를 JSON으로 기록한다.
- 기존 GUI 아이콘, 팔레트, EXE는 변경하지 않는다.

## 3. 구현 방향

- `tools/scripts/generate_fq4_class_index_maps.py`를 추가한다.
- `extract_fq4_class_icons.py`의 레이아웃 규칙을 재사용해 2x2, 3x3, 4x4, 6x6, 8x8 예외를 같은 기준으로 렌더링한다.
- 후보 CLASS별 사용 인덱스 집합을 계산한다.
- 랜덤 seed를 고정해 재현 가능한 방식으로 10개를 선택한다.
- 선택 기준은 새로 추가되는 인덱스 수가 큰 항목을 우선하되, 같은 유형만 몰리지 않도록 섞는다.

## 4. 산출물

- `docs/fq4/analysis/032/class-NNN-index-map.png`
- `docs/fq4/analysis/032/random-index-map-samples.png`
- `docs/fq4/analysis/032/index-map-sample-report.json`

## 5. 검증

- 선택된 CLASS 수가 10개인지 확인한다.
- 각 이미지가 숫자를 읽을 수 있는 크기로 생성되는지 확인한다.
- 각 CLASS의 대표 프레임 레이아웃이 현재 `class_catalog.json`과 맞는지 확인한다.
- 기존 원본 ROM과 세이브 파일은 수정하지 않는다.

## 6. 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 하며 수정하지 않는다. ROM 전체 복사본은 만들지 않는다.

## 7. 완료 조건

- 랜덤 샘플 10개의 인덱스 지도 이미지가 생성된다.
- 선택된 CLASS와 인덱스 집합이 문서화된다.
- 완료 문서가 작성된다.
