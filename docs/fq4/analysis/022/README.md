# PLAN-022 누락 캐릭터 및 이름표 분석

## 원인

트리스렌은 세이브에서 누락된 것이 아니었다. `memcard/retroarch/fq4-kor-250826.srm`의 두 슬롯 모두 `record 246`에 존재한다.

| 항목 | 값 |
|---|---:|
| name ID | 265 |
| CLASS ID | 198 |
| CLASS | `ナイト` / KNIGHT |
| LV | 58 |
| HP | 608 |
| HR | 9 |
| AT | 53 |
| AR | 57 |
| DF | 49 |
| DR | 59 |

기존 에디터는 CLASS를 0~149로 제한했기 때문에 CLASS 198인 이 레코드를 숨겼다. 동시에 character name ID 265를 패치 ROM의 사용자 정의 한글 바이트로 잘못 디코딩해 이름표가 깨져 있었다.

## 전체 표 재검증

원본 PS-X EXE에서 다음 고정 표를 확인했다.

- 캐릭터 이름: EXE `0xE86B0`, 640개, 항목당 10바이트
- CLASS 이름: EXE `0xEA064`, 220개, 항목당 9바이트
- CLASS 그래픽: `/CHR0/C00.P`부터 `/CHRD/CDB.P`까지 ID 0~219

CLASS ID 220부터는 이름 문자열이 아니라 다른 바이너리 데이터이므로 유효 범위는 0~219다. 이름표는 한글패치 ROM이 아닌 일본판 원본을 CP932로 디코딩하고 반각 가타카나를 NFKC 정규화했다. 이 방식으로 기존 100개의 깨진 비 ASCII 이름을 읽을 수 있는 일본어 표기로 복구했다. 사용자 화면으로 확인된 name ID 265는 `트리스렌 / トリスラム`으로 병기했다.

## 표시 결과

| 카드 | 슬롯당 기존 표시 | 슬롯당 수정 표시 |
|---|---:|---:|
| MCD 표본 | 419 | 521 |
| RetroArch SRM | 409 | 511 |

각 슬롯에서 CLASS 150~219의 유효 레코드 102개가 추가로 표시된다. CLASS 220 이상인 1개 레코드, HP 0 레코드와 범위를 벗어난 name ID 레코드는 계속 제외한다.

축약 CLASS 그래픽 10개는 16~19 타일이 없으므로 실제 0~3 타일의 첫 대표 프레임을 조합한다. 나머지는 승인된 16~19 앞모습 조합을 유지한다.

## 자료

- `save-record-audit.json`: 수정 전 조사
- `save-record-audit-after.json`: 수정 후 조사
- `tools/scripts/analyze_fq4_character_names.py`
- `tools/scripts/generate_fq4_editor_names.py`
