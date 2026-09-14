# FQ4-PLAN-014 — 향후 한글패치 xdelta 자동 호환 계획

- 작성일: 2026-09-13
- 상태: **완료**
- 선행 결과: [FQ4-FINISH-013](../finish/013-independent-edc-ecc-repair.md)
- 현재 지원: `250826` xdelta SHA-256 고정
- 완료 문서 예정: `docs/fq4/finish/014-future-xdelta-compatibility.md`

## 1. 목적

앞으로 새로운 퍼스트퀸4 한글패치 xdelta가 배포돼도 GUI/EXE를 날짜별로 다시 만들지 않고 적용할 수 있도록 변환 엔진을 구조 기반으로 변경한다.

새 방식은 xdelta 파일명, 날짜와 패치 SHA-256을 허용 목록으로 제한하지 않는다. 일본판 원본에 사용자가 선택한 xdelta를 먼저 적용하고, 결과 ROM에서 필요한 실행 파일, 훅 위치, 코드 공간, DUMMY.DUM과 sector 형식을 직접 검사한다. 구조가 호환되면 일반 BIOS용 변환을 적용하고, 안전성을 증명할 수 없으면 출력 없이 중단하며 정확한 불일치 항목을 표시한다.

## 2. 지원 원칙

- 일본판 원본 BIN의 SHA-256 검사는 유지한다.
- 한글 BIOS의 SHA-256과 글꼴 구조 검사는 유지한다.
- xdelta의 파일명, 날짜와 SHA-256 제한은 제거한다.
- xdelta 적용 결과의 고정 전체 SHA-256 검사는 제거한다.
- 전체 ROM 크기, raw sector 구조, ISO 파일 목록과 실행 파일 identity를 검사한다.
- 변환에 필요한 각 위치는 고정 offset 하나만 신뢰하지 않고 byte signature와 주변 제어 흐름으로 확인한다.
- 알려진 241112와 250826을 회귀 프로필로 사용한다.
- 미래 패치가 실행 파일 구조를 바꿔 자동 판정이 불가능하면 추측해서 쓰지 않고 `호환되지 않는 패치 구조`로 거부한다.

“모든 미래 패치를 무조건 적용”하는 방식은 안전하지 않다. 이 작업의 목표는 기존 핵심 구조를 유지한 새 번역·스크립트 패치를 자동 수용하고, 구조 변경 패치는 손상 없이 거부하는 것이다.

## 3. 동적 호환성 검사

### A. 디스크와 ISO

- 출력 크기가 2,352바이트 sector 단위인지 확인한다.
- sync, MSF header, Mode 2 Form 1/2와 XA subheader를 전수 검사한다.
- ISO9660에서 `SLPS_006.04`와 `DUMMY.DUM`을 이름으로 찾는다.
- DUMMY.DUM이 최소 35개 연속 Form 1 sector를 제공하는지 확인한다.
- 고정 LBA 24184를 우선 기대하되 extent가 이동했으면 새 LBA를 loader 코드에 반영한다.
- 실행 파일 크기, PS-X EXE header와 load address를 확인한다.

### B. 실행 코드 signature

다음 대상을 명령어 signature와 호출 관계로 찾는다.

- 기존 BIOS `B0(51h)` 글리프 조회 wrapper
- 게임 CD read wrapper와 ABI
- 메모리 pool 초기화 호출과 pool 크기 전역
- loader 호출을 삽입할 초기화 지점
- 조회 훅 주변의 원본 명령
- 일반 BIOS loader와 lookup 코드를 넣을 안전한 code cave

고정 주소와 signature 결과가 일치하면 기존 프로필을 사용한다. 주소가 이동했지만 유일한 signature와 호출 관계가 확인되면 새 주소로 코드를 조립한다. signature가 없거나 여러 개면 중단한다.

### C. 글꼴과 문자열 domain

- 한글 BIOS `0x69D68`부터 70,500바이트 글꼴 해시와 2,350자 구조를 검사한다.
- 패치된 실행 파일의 한글 코드가 기존 Shift-JIS 위치 기반 domain을 사용하는지 표본과 정적 문자열로 확인한다.
- 문자 인코딩 방식이 바뀌었으면 기존 lookup을 적용하지 않고 호환 불가로 판정한다.

## 4. EDC/ECC 일반화

현재의 고정 교정 범위 `10030..22652`와 예상 개수 11,046 제한을 제거한다.

1. xdelta 적용 직후 전체 43,002개 sector를 검사한다.
2. Mode 2 Form 1에서 실제로 실패한 EDC/P/Q tail만 교정한다.
3. 일반 BIOS용 코드를 적용한 뒤 전체 sector를 다시 검사한다.
4. sync, header 또는 XA subheader 오류는 자동으로 덮지 않고 입력 호환 오류로 중단한다.
5. Form 2 sector에는 Form 1 ECC를 생성하지 않는다.
6. 최종 EDC, P, Q 오류가 모두 0일 때만 출력으로 확정한다.

교정 LBA와 개수는 패치 버전별 결과 보고서에 기록하며 고정값과 일치할 필요가 없다.

## 5. 빌드 프로필

변환 엔진에 다음 두 계층을 둔다.

- **구조 프로필:** 실행 파일 signature, ABI, code cave 조건과 patch writer
- **입력 관찰 결과:** ISO extent, 발견 주소, 기존 sector 오류와 최종 결과

250826은 현재 검증 프로필로 등록한다. 241112는 별도 분석해 같은 구조 프로필로 처리 가능한지 확인한다. 두 패치에서 공통인 조건만 필수 signature로 남기고 번역 데이터나 전체 ROM 해시는 조건에서 제외한다.

새 패치가 같은 프로필을 통과하면 GUI에는 `호환 구조 확인됨`으로 표시한다. 실패하면 날짜가 아니라 실패한 구조 조건을 표시한다.

## 6. GUI 변경

- `250826 한글패치` 표기를 `한글패치 xdelta`로 변경한다.
- 선택 직후에는 `검사 전`, 적용·분석 후에는 `호환`, `호환 불가` 상태를 표시한다.
- 성공 화면에 입력 xdelta SHA-256, 감지한 구조 프로필, 교정한 sector 개수와 결과 BIN SHA-256을 표시한다.
- 고정 결과 SHA-256 대신 전체 구조·EDC/ECC 검증 통과 여부를 성공 기준으로 사용한다.
- 상세 로그에 발견한 실행 파일 주소와 실패 조건을 기록한다.
- 기존 출력 보호, 취소와 임시 BIN 한 개 정책은 유지한다.

## 7. 검증 대상

### 알려진 패치

| xdelta | 기대 결과 |
|---|---|
| `241112` | 구조 분석 후 호환 또는 구체적 비호환 사유 확정 |
| `250826` | 기존 화면·글꼴·EDC/ECC 결과 유지 |

### 변형 시험

- xdelta 파일명을 임의로 바꿔도 같은 결과가 나오는지 확인한다.
- 패치 파일의 날짜 metadata가 달라도 해시 제한 없이 처리되는지 확인한다.
- 실행 파일 훅 1바이트, DUMMY extent, 글꼴 domain을 각각 의도적으로 다르게 만든 작은 구조 fixture로 안전 거부를 검사한다.
- EDC/ECC 오류 개수와 범위가 다른 입력에서 전체 자동 교정을 검사한다.
- 한글·공백 경로, 취소, 덮어쓰기와 임시 파일 정리를 다시 확인한다.

전체 ROM fixture를 여러 벌 저장하지 않고 byte patch 목록과 작은 sector sample만 보관한다.

## 8. 원본 보존과 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 읽기 전용이다.
- 전체 작업 ROM은 `work/fq4/rom/current.bin` 한 벌만 유지한다.
- 241112/250826 비교는 임시 BIN 한 개를 번갈아 사용하고 검사 직후 삭제한다.
- GUI와 EXE 결과 검증도 같은 임시 출력 경로를 재사용한다.
- 실패·취소 시 임시 전체 ROM과 검사 report directory를 제거한다.
- 분석·변환·검증 스크립트는 `tools/scripts/`에 작성한다.
- GUI와 최종 EXE는 기존 경로에서 같은 파일로 교체한다.

## 9. 통과 기준

- xdelta 파일명·날짜·SHA-256 고정 제한이 제거된다.
- 250826 패치 결과의 화면, 글꼴, 전체 EDC/ECC가 유지된다.
- 241112의 호환 여부가 구조 검사로 정확히 판정된다.
- 같은 핵심 구조를 유지하는 미등록 xdelta가 별도 코드 변경 없이 처리된다.
- 구조가 달라 안전성을 증명할 수 없는 패치는 ROM을 남기지 않고 거부된다.
- 최종 BIN의 sync, header, subheader, EDC, P와 Q 오류가 모두 0이다.
- Python GUI와 단일 EXE가 같은 판정을 내린다.
- 원본이 보존되고 전체 임시 ROM이 누적되지 않는다.

## 10. 산출물

- `tools/scripts/fq4_patch_profile.py`: 구조 signature 검색 및 프로필 판정
- 일반화된 `build_fq4_bios_independent.py`
- 갱신된 `tools/fq4_bios_independent_gui.py`
- 갱신된 `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- `docs/fq4/analysis/014/profile-241112.json`
- `docs/fq4/analysis/014/profile-250826.json`
- `docs/fq4/analysis/014/compatibility-tests.json`
- `docs/fq4/analysis/014/ecc-tests.json`
- `docs/fq4/analysis/014/README.md`
- `docs/fq4/finish/014-future-xdelta-compatibility.md`

## 11. 사용자 확인

- 승인 상태: **승인 — 2026-09-14 작업 재개**
- 승인 시 실행 범위: 241112/250826 구조 비교, signature 기반 프로필 구현, 전체 EDC/ECC 동적 교정, GUI·EXE 갱신과 회귀 검증
- 미래 패치 처리 원칙: 구조 검사를 모두 통과하면 자동 적용하고, 구조가 달라진 패치는 파일을 손상시키지 않고 구체적 사유와 함께 거부
