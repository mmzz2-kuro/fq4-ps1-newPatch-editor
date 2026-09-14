# FQ4-PLAN-013 — 독립 EDC/ECC 검사 및 배드섹터 교정 계획

- 작성일: 2026-09-13
- 상태: **사용자 확인 대기**
- 사용자 발견: GUI 생성 BIN을 외부 ECC/EDC 검사기로 검사하면 배드섹터가 보고됨
- 현재 작업 ROM: `work/fq4/rom/current.bin`
- 현재 SHA-256: `95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e`
- 완료 문서 예정: `docs/fq4/finish/013-independent-edc-ecc-repair.md`

## 1. 문제 정의

기존 빌더와 검증기가 같은 `fix_form1()` 구현을 사용했다. 따라서 해당 구현의 Mode 2 Form 1 EDC 또는 P/Q ECC 계산이 잘못돼도 빌드와 자체 검증이 함께 통과할 수 있다. PLAN-010~012의 “EDC/ECC 통과” 판정은 독립 구현으로 재검증될 때까지 철회한다.

원본 일본판, 250826 xdelta 적용 직후 ROM, 현재 일반 BIOS용 ROM을 서로 독립적인 검사기로 비교해 다음을 구분한다.

1. 원본부터 존재하는 의도적·기존 불량 sector
2. 250826 한글패치가 만든 sector 오류
3. 일반 BIOS용 로더·글꼴 삽입 과정에서 새로 만든 sector 오류
4. CUE track mode 또는 검사기의 sector 해석 차이

## 2. 승인 범위

- workspace에 사용 가능한 독립 EDC/ECC 검사 도구와 구현을 조사한다.
- 최소 두 경로로 검사한다: 프로젝트 구현과 독립 도구 또는 별도 검증된 알고리즘.
- 원본, 250826 적용 직후, PLAN-010 결과의 sector별 EDC/ECC 상태를 비교한다.
- 배드섹터의 LBA, Mode, Form, subheader, EDC, P parity와 Q parity를 각각 기록한다.
- `fix_form1()`의 계산 범위, 주소 입력, zero 영역과 parity 순서를 표준 CD-ROM XA 방식과 대조한다.
- 오류를 확정하면 공용 sector 재계산 함수를 수정한다.
- 현재 `current.bin`, Python GUI 엔진과 단일 EXE를 같은 수정으로 재빌드한다.
- 외부 검사에서 배드섹터가 없어졌는지 확인한다.

번역문, 글꼴 모양, loader 주소와 문자 lookup은 변경하지 않는다.

## 3. 보존 및 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 읽기 전용이다.
- 전체 작업 ROM은 `work/fq4/rom/current.bin` 한 개를 계속 재사용한다.
- 비교 대상 전체 ROM을 여러 벌 보존하지 않는다.
- 250826 중간본은 임시 BIN 한 개로 생성하고 sector 검사 결과를 기록한 즉시 삭제한다.
- 수정 검증용 GUI/EXE 출력도 임시 BIN 한 개만 사용하고 검사 직후 삭제한다.
- sector sample은 전체 ROM 대신 LBA 번호, 2,352바이트 sector 해시와 필요한 작은 byte 범위만 저장한다.
- 분석·복구·검증 스크립트는 `tools/scripts/`에 작성한다.
- 사용자 GUI는 기존 `tools/` 위치를 유지한다.

## 4. 독립 검사 방법

### A. 기준선 분리

다음 세 상태를 동일한 검사 조건으로 조사한다.

| 상태 | 목적 |
|---|---|
| 일본판 원본 BIN | 원래 존재하는 sector 상태 확인 |
| 250826 xdelta 직후 | 기존 한글패치가 추가한 오류 분리 |
| 현재 PLAN-010 BIN | 일반 BIOS 변환이 추가한 오류 분리 |

각 BIN은 모든 2,352바이트 sector를 검사하되 결과에는 실패 LBA만 기록한다.

### B. sector 구성요소별 판정

Mode 2 sector마다 다음을 별도 판정한다.

- sync pattern과 BCD MSF header
- duplicated XA subheader 8바이트
- Form 1/Form 2 구분
- Form 1 EDC 입력 범위와 저장 위치
- ECC 계산 전 address 4바이트 처리 방식
- P parity 172바이트
- Q parity 104바이트
- Form 2 EDC와 오디오/XA sector의 비개입

현재 빌더가 실제로 수정한 LBA `32`, `254`, `466`, `24184..24218`을 우선 확인하되 전체 디스크 검사로 누락을 막는다.

### C. 교차 검증

- 외부 검사 도구의 실패 LBA와 자체 독립 구현의 실패 LBA가 일치해야 한다.
- 가능하면 `eccedc` 계열 도구 또는 CD-ROM XA 규격을 구현한 검증된 도구를 사용한다.
- 외부 실행 파일을 새로 받아야 한다면 출처와 SHA-256을 기록하고 설치 전에 필요한 승인 절차를 따른다.
- 도구마다 “의도적 bad sector” 처리 정책이 다르면 EDC, P, Q 결과를 원시 값으로 비교한다.

## 5. 예상 조사 지점

현재 `fix_form1()`에서 특히 다음 오류 가능성을 확인한다.

1. Mode 2 Form 1 EDC가 `subheader+user data` 대신 잘못된 시작 위치를 포함하는지
2. ECC를 계산할 때 Mode 2 address field를 zero 처리해야 하는 규칙을 빠뜨렸는지
3. EDC를 쓴 뒤 P를 계산하고, P까지 포함한 상태에서 Q를 계산하는 순서가 맞는지
4. Q 계산 source 범위가 P parity를 포함하는지
5. XA subheader 두 복사본이 일치하지 않는 sector를 그대로 재계산했는지
6. 수정되지 않은 Form 2 또는 XA audio sector에 Form 1 알고리즘을 적용했는지

이는 가설이며 독립 검사 결과로 확정하기 전에는 ROM 수정에 사용하지 않는다.

## 6. 복구 절차

1. 독립 검사로 최초 불일치 구성요소를 확정한다.
2. `tools/scripts/`의 공용 EDC/ECC 구현을 규격에 맞게 교정한다.
3. 알려진 독립 test vector 또는 원본 정상 sector로 P/Q byte 전체를 검증한다.
4. `current.bin`을 검증된 250826 입력에서 같은 파일로 재구성한다.
5. 실행 파일 및 35개 글꼴 sector만 다시 적용한다.
6. 변경 sector의 EDC/P/Q를 교정된 함수로 생성한다.
7. 전체 디스크를 독립 검사기로 재검사한다.
8. GUI 엔진이 같은 공용 함수를 사용하도록 확인한다.
9. 단일 EXE를 같은 `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`로 교체한다.
10. EXE 생성 ROM도 독립 검사기로 다시 검사한다.

## 7. 검증 기준

### 필수 통과

- 원본에서 정상인 sector가 최종 ROM에서도 모두 정상이다.
- 일반 BIOS 변환이 새로 만든 EDC, P 또는 Q 오류가 0개다.
- 외부 도구와 독립 구현의 실패 LBA가 일치한다.
- 수정 sector의 저장된 EDC/P/Q가 독립 계산 결과와 byte 단위로 일치한다.
- ISO 파일, DUMMY.DUM extent, ROM 크기와 CUE `MODE2/2352`가 유지된다.
- 일반 BIOS에서 `font_ready=1`, 전체 글꼴 해시와 대표 13자 GPU 업로드가 유지된다.
- 사용자가 사용한 ECC/EDC 검사에서도 배드섹터가 나오지 않는다.
- Python GUI와 EXE 결과가 같은 SHA-256을 생성한다.

원본이나 250826 패치부터 존재하는 의도적 오류가 확인되면 “새 오류 0개”와 기존 오류 목록을 분리해 보고하며, 임의로 기존 보호 sector를 고치지 않는다.

## 8. 산출물

- `tools/scripts/verify_cdrom_xa_ecc.py`: 독립 전수 검사기
- 교정된 공용 EDC/ECC 생성 코드
- `docs/fq4/analysis/013/baseline-comparison.json`: 세 상태 실패 LBA 비교
- `docs/fq4/analysis/013/component-diff.json`: EDC/P/Q 구성요소별 결과
- `docs/fq4/analysis/013/external-verification.json`: 외부 도구 결과
- `docs/fq4/analysis/013/rom-verification.json`: 교정 ROM 전체 검사
- `docs/fq4/analysis/013/exe-verification.json`: EXE 생성 ROM 검사
- `docs/fq4/analysis/013/README.md`: 원인과 재현 방법
- `docs/fq4/finish/013-independent-edc-ecc-repair.md`: 완료 문서

## 9. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: 독립 전체 sector 검사, 공용 알고리즘 교정, current ROM·GUI·EXE 재빌드와 외부 검증
- ROM 쓰기 조건: 원본/250826/현재 상태 비교로 새 오류와 기존 오류를 분리한 뒤에만 수행
