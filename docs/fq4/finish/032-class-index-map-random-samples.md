# FQ4-FINISH-032 CLASS 인덱스 지도 랜덤 샘플 생성
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/032-class-index-map-random-samples.md`
- 대상 스크립트: `tools/scripts/generate_fq4_class_index_maps.py`

## 결과

CLASS별 팔레트 보정에 사용할 숫자 인덱스 지도 샘플을 생성했다. 현재 대표 프레임 레이아웃 규칙을 그대로 사용해 스프라이트 픽셀 인덱스 값을 이미지 위에 표시했다.

랜덤 seed는 `20260914`로 고정했다. 선택된 10개 샘플은 합산 120개의 팔레트 인덱스를 덮는다.

## 선택 샘플

| CLASS | 이름 | 고유 인덱스 수 |
|---:|---|---:|
| 018 | 프리스트(얀샤프) | 42 |
| 026 | 왕자(알프레드-후) | 33 |
| 062 | C・골렘(구름) | 14 |
| 123 | 물의왕 | 63 |
| 143 | 빅풋 | 16 |
| 148 | 토드(개구리) | 29 |
| 179 | マンイーター | 7 |
| 191 | [말]왕(아레스-후)-[카리온] | 66 |
| 199 | 드래곤(머리) | 22 |
| 215 | 그리폰 | 66 |

## 산출물

- `docs/fq4/analysis/032/random-index-map-samples.png`
- `docs/fq4/analysis/032/index-map-sample-report.json`
- `docs/fq4/analysis/032/class-018-index-map.png`
- `docs/fq4/analysis/032/class-026-index-map.png`
- `docs/fq4/analysis/032/class-062-index-map.png`
- `docs/fq4/analysis/032/class-123-index-map.png`
- `docs/fq4/analysis/032/class-143-index-map.png`
- `docs/fq4/analysis/032/class-148-index-map.png`
- `docs/fq4/analysis/032/class-179-index-map.png`
- `docs/fq4/analysis/032/class-191-index-map.png`
- `docs/fq4/analysis/032/class-199-index-map.png`
- `docs/fq4/analysis/032/class-215-index-map.png`

## 검증

다음 검증을 수행했다.

- `python tools/scripts/generate_fq4_class_index_maps.py`
- `python -m py_compile tools/scripts/generate_fq4_class_index_maps.py`
- 출력 샘플 수 10개 확인
- 커버 인덱스 120개 확인
- 종합 확인 이미지 `random-index-map-samples.png` 확인

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. GUI 아이콘과 EXE도 이번 작업에서는 변경하지 않았다.
