# FQ4-FINISH-016 — 부대 종족 제한 확장 선택 옵션 통합 완료

- 완료일: 2026-09-14
- 대응 계획: [FQ4-PLAN-016](../plans/016-optional-party-race-limit-gui.md)
- 상태: **완료**
- 결과 EXE: `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- EXE SHA-256: `c46feb6eeff3f17b1ed9eccb256df08315891c564d53a113843262fbed50e397`

## 완료 내용

PLAN-015 종족 제한 변경을 독립 패치 모듈로 정리하고 기존 BIOS 독립 한글패치 GUI에 선택 기능으로 연결했다.

- 체크박스 기본값: 해제
- 체크 해제: 기존 BIOS 독립 한글패치만 적용
- 체크 선택: BIOS 독립 한글패치와 종족 그래픽 예산 확장을 함께 적용
- GUI 표시: `부대 종족 제한을 18종 수준으로 확장 (실험적)`
- 명령행 인자: `--expand-party-species-limit`
- 독립 CLI: `tools/scripts/build_party_race_limit_patch.py`

GUI 설명에는 실제 제한이 고정 10종 배열이 아니라 종족별 그래픽 비용 합계이며, 장시간 플레이 검증이 더 필요하다는 내용을 표시했다.

## 구현 결과

`build_party_race_limit_patch.py`는 인메모리 적용 함수와 트랜잭션 파일 CLI를 제공한다. 8개 비교 명령의 사전 값을 확인한 뒤에만 `0x1E0`에서 `0x361`로 바꾸고, 변경한 7개 raw sector의 EDC/P/Q를 즉시 갱신한다. 중복 적용과 알 수 없는 사전 값은 오류로 중단한다.

공통 BIOS 독립 빌드 엔진은 선택 여부에 따라 기대 최종 해시를 구분한다. 체크 해제 경로가 이전 결과와 달라지거나 체크 선택 경로가 PLAN-015 결과와 다르면 완성 파일을 배치하지 않는다. frozen EXE에도 같은 모듈과 검증 조건을 포함했다.

## 검증 결과

| 실행 경로 | 선택 | 결과 SHA-256 | 결과 |
|---|---:|---|---|
| Python 엔진 | 해제 | `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d` | 통과 |
| Python 엔진 | 선택 | `684d47b644f961b6552c311dffe577418f0b74ba109da7c6c25d57838beeba31` | 통과 |
| 단일 EXE | 해제 | `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d` | 통과 |
| 단일 EXE | 선택 | `684d47b644f961b6552c311dffe577418f0b74ba109da7c6c25d57838beeba31` | 통과 |

체크 해제 결과는 기존 BIOS 독립 결과와 바이트 단위로 동일하다. 체크 선택 결과는 사용자가 작동을 확인한 PLAN-015 작업 ROM과 바이트 단위로 동일하다.

두 Python 결과와 최종 EXE 선택 결과의 전체 43,002개 sector 검사에서 sync, header, subheader, EDC, P와 Q 오류가 모두 0이었다. 선택 결과의 8개 비교 명령도 기대값과 일치했다. CUE는 결과 BIN 이름과 `MODE2/2352`를 정확히 참조했다.

## 원본과 용량 관리

`original/`, `patched/`, `korean-patch/`와 BIOS는 변경하지 않았다. 검증에는 `work/fq4/016/test.bin` 한 개를 순차 재사용했고 완료 후 BIN/CUE를 제거했다. 기존 `work/fq4/rom/current.bin`은 변경하지 않았다. 최종 EXE는 같은 파일명으로 교체해 사본을 누적하지 않았다.

## 남은 플레이 확인

기본 동작은 사용자가 확인했다. 서로 다른 종족을 많이 포함한 부대로 이동, 전투, 합류·분리, 이벤트 편성과 세이브·로드를 장시간 반복하는 검증은 남아 있다. 이 확인이 끝날 때까지 GUI에서 해당 옵션을 실험 기능으로 표시한다.

## 산출물

- `tools/scripts/build_party_race_limit_patch.py`
- `tools/scripts/build_fq4_bios_independent.py`
- `tools/fq4_bios_independent_gui.py`
- `tools/scripts/test_fq4_frozen_engine.py`
- `tools/packaging/fq4_gui.spec`
- `tools/README-fq4-gui.md`
- `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- `docs/fq4/analysis/016/build-matrix.json`
- `docs/fq4/analysis/016/exe-verification.json`
- `docs/fq4/analysis/016/README.md`
