# FQ4-FINISH-017 PS1 세이브 에디터

- 완료일: 2026-09-14
- 상태: **구현 및 정적 검증 완료, 게임 내 사용자 검증 대기**
- 결과물: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 완료한 작업

PS1 raw 메모리카드의 디렉터리와 4블록 FQ4 세이브 체인을 읽고, 캐릭터의 CLASS·FT·LV·HP·HR·AT·AR·DF·DR을 편집해 새 `.mcd`로 저장하는 Windows GUI를 만들었다. ROM의 640개 캐릭터 이름표와 150개 전체 CLASS 표를 포함한다. 두 FQ4 슬롯을 자동 탐지하며, 원본 경로를 기본 출력으로 사용하지 않는다. 같은 경로를 선택한 경우에는 별도의 덮어쓰기 확인을 요구한다.

저장 엔진은 FQ4 payload의 8개 페이지 XOR 체크섬을 다시 계산하고 임시 파일에 먼저 쓴 뒤 원자적으로 배치한다. 배치 후 파일을 다시 열어 카드 구조와 모든 게임 체크섬을 검증한다. FQ4가 아닌 카드 데이터와 PS1 디렉터리 영역은 바이트 단위로 보존한다.

## 검증 결과

- 입력을 변경하지 않은 왕복 결과가 원본과 완전히 일치했다.
- 슬롯 1, 레코드 229의 종족 ID를 9에서 10으로 바꾼 통제 시험에서 종족 1바이트와 내부 체크섬 1바이트만 변경됐다.
- 손상된 payload는 체크섬 오류로 거부됐다.
- 빌드한 단일 EXE가 Windows에서 정상적으로 프로세스와 GUI를 시작했다.
- 사용자 제공 2번 슬롯 화면의 12개 표시 행과 이름·CLASS·LV·HP·HR·AT·AR·DF·DR 값이 일치했다.
- 잘못된 HP 위치와 불완전한 종족명 표를 수정했으며, 2번 슬롯에서 419개 유효 캐릭터 레코드를 표시한다.
- 원본 `memcard/`, `savestates/`, `dos-save/`, `original/`, `patched/`, `korean-patch/` 파일은 수정하지 않았다.

시험본은 `work/fq4/save-editor/current-test.mcd` 한 개만 유지한다. 이 파일은 MIMIC 종족을 BALESTA로 바꾼 검증용이므로 실제 플레이 세이브로 사용하지 않는 편이 좋다.

## 남은 사용자 검증

에디터로 별도 저장한 메모리카드를 DuckStation에서 로드해 다음을 확인해야 한다.

1. 바꾼 FT·HP·AT·AR·DF·DR 값이 캐릭터 화면과 전투에 반영되는지 확인한다.
2. 종족 변경 후 캐릭터 화면, 지도 외형, 이동과 전투 진입·종료를 확인한다.
3. 게임에서 다시 저장한 뒤 재로드되는지 확인한다.

이 검증에서 필드 의미나 종족별 동작 문제가 발견되면 PLAN-017의 결함으로 이어서 수정한다.

## 산출물

- `tools/scripts/fq4_memcard.py`
- `tools/scripts/analyze_fq4_save.py`
- `tools/scripts/verify_fq4_save.py`
- `tools/scripts/test_fq4_memcard.py`
- `tools/FQ4SaveEditor/`
- `tools/dist/FQ4-PS1-Save-Editor.exe`
- `docs/fq4/analysis/017/`
