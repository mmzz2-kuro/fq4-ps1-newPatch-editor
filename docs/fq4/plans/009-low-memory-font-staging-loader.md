# FQ4-PLAN-009 — 저주소 staging buffer 글꼴 로더 계획

- 작성일: 2026-09-13
- 상태: **사용자 확인 대기**
- 선행 결과: [FQ4-FINISH-008](../finish/008-deferred-font-loader-hook.md)
- 작업 ROM: `work/fq4/rom/current.bin` 한 벌
- 시작 SHA-256: `b3000a9795faf1851af261732bc61208be7d76a0ddaf3a9fa118225a458fb241`
- 완료 문서 예정: `docs/fq4/finish/009-low-memory-font-staging-loader.md`

## 1. 목적

CD 라이브러리가 높은 heap 주소 `0x801E6528`에 데이터를 남기지 않는 원인을 교차 시험으로 분리한다. 정상 PVD 읽기에서 검증된 낮은 주소대의 2,048바이트 staging buffer로 글꼴 sector를 한 개씩 읽고, CPU 복사로 예약된 상주 글꼴 영역에 옮기는 로더를 구현한다.

최종 목표는 35개 sector의 71,680바이트 payload가 상주 영역에 정확히 복사되고, 70,500바이트 글꼴 해시와 `FQ4F` trailer가 일치해 `font_ready=1`이 되는 것이다.

## 2. 현재 확인된 사실

- `0x8008F600`의 ABI는 `(sector 수, ISO 논리 LBA, RAM 목적지)`이다.
- raw LBA 24184의 wrapper 입력은 논리 LBA 24034이다.
- `(1, 24034..24068, high_address)` 호출은 35개 sector를 오류 없이 읽지만 높은 목적지 데이터가 변하지 않는다.
- 정상 `(1, 16, 0x801179BC)` PVD 호출은 낮은 목적지에 올바른 데이터가 남는다.
- 글꼴 payload는 35 sector, 71,680바이트이며 상주 예약도 71,680바이트가 필요하다.
- 전체 글꼴은 payload 선두 70,500바이트이고 `FQ4F` trailer는 offset `0x11364`에 있다.

## 3. 승인 범위

- PVD를 높은 글꼴 주소로 읽는 시험과 글꼴 sector를 검증된 낮은 버퍼로 읽는 시험을 수행한다.
- 실패 조건이 sector 내용인지 목적지 주소인지 분리한다.
- 게임 초기화와 로더 실행 동안 안전한 2,048바이트 staging buffer를 선정한다.
- 각 sector를 staging buffer로 읽고 CPU로 상주 영역에 복사하는 루프를 구현한다.
- staging buffer와 기존 게임 구조의 사용 시점·수명을 확인한다.
- 상주 영역 71,680바이트 예약, magic 검사, 상태와 조회 훅을 검증한다.
- 같은 `current.bin`을 PLAN-004 상태로 재구성한 뒤 수정본을 한 번 적용한다.
- 일반 BIOS에서 RAM 해시, 실제 글리프 조회·변환·GPU 업로드를 검사한다.
- 결과를 완료 문서에 기록한다.

배포용 xdelta, GUI, 번역문 변경과 실기 최종 검증은 포함하지 않는다.

## 4. 보존 및 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 읽기 전용이다.
- 전체 ROM은 `work/fq4/rom/current.bin` 하나만 유지한다.
- 새 BIN·ISO·IMG나 보존용 ROM 복사본을 만들지 않는다.
- 재빌드는 같은 ROM을 PLAN-004 상태로 복원한 뒤 수정된 빌드를 적용한다.
- 모든 입력 해시, 훅 원본 명령, RAM 범위와 변경 sector를 쓰기 전에 검사한다.
- 분석·변환·빌드·검증 스크립트는 `tools/scripts/`에 작성한다.
- 전체 RAM dump를 반복 보존하지 않고 해시, 주소와 작은 sample만 `work/fq4/009/`에 남긴다.

## 5. 교차 시험

### A. 주소와 sector 조건 분리

다음 네 경우를 같은 cold boot 조건에서 비교한다.

| 시험 | sector | 목적지 | 판정 목적 |
|---|---|---|---|
| A | PVD raw LBA 166 | `0x801179BC` | 기존 정상 기준 |
| B | PVD raw LBA 166 | 높은 예약 주소 | 높은 주소 쓰기 가능 여부 |
| C | 글꼴 raw LBA 24184 | `0x801179BC` | 글꼴 sector 자체의 읽기 가능 여부 |
| D | 글꼴 raw LBA 24184 | 신규 staging 후보 | 제품용 후보 검증 |

각 시험에서 wrapper 진입 인자, CD 로그, 반환값, 목적지 전후 해시와 첫 64바이트를 기록한다. B만 실패하면 주소 제약, C도 실패하면 sector 서브헤더·mode 또는 필터 조건을 추가 조사한다.

### B. staging buffer 선정

후보는 다음 조건을 만족해야 한다.

- 2,048바이트 이상이고 4바이트 정렬이다.
- 글꼴 로더 실행 중 다른 초기화·CD·GPU·메모리카드 작업과 겹치지 않는다.
- sector 반환 직후 CPU 복사가 끝날 때까지 유지된다.
- 기존 전역 포인터나 callback 구조를 손상하지 않는다.
- 원래 버퍼를 빌려 쓰면 사용 전후 필요한 내용을 보존하거나 사용이 끝난 시점을 증명한다.

검증된 `0x801179BC`를 우선 조사하되 크기와 주변 구조의 소유권이 불명확하면 그대로 제품용으로 사용하지 않는다. 게임 pool의 낮은 부분에서 2,048바이트를 별도 예약하거나 기존 파일 로더 buffer를 재사용하는 대안을 비교한다.

## 6. 로더 설계

1. 게임 pool에서 상주 글꼴 71,680바이트와 필요 시 staging 2,048바이트를 겹치지 않게 예약한다.
2. 상태를 `미시도`, `진행 중`, `성공`, `실패`로 구분해 재진입을 막는다.
3. index 0부터 34까지 `0x8008F600(1, 24034+index, staging)`을 호출한다.
4. 각 호출 성공 직후 정확히 2,048바이트를 `font_base + index*2048`로 CPU 복사한다.
5. R3000A에 맞는 정렬 word 복사를 기본으로 하고 나머지 byte 처리를 명시한다.
6. 35회 완료 후 `font_base+0x11364`의 `FQ4F`를 검사한다.
7. 성공하면 상태를 성공으로 바꾸고, 실패하면 같은 세션에서 재시도하지 않고 BIOS fallback을 유지한다.
8. staging buffer를 pool에서 예약했다면 게임 allocator에 노출되는 크기에서 함께 제외한다.

CPU 복사 루프는 load delay와 branch delay slot을 모두 명시적으로 처리한다.

## 7. RAM 안전성 검사

- 실제 malloc 결과를 기준으로 pool 시작·종료와 상주 글꼴·staging 주소를 계산한다.
- 모든 영역이 `0x801F7FF0` 아래에 있고 stack reserve와 겹치지 않아야 한다.
- 게임 custom allocator의 최대 사용 주소를 전투·지도·세이브 로드에서 관찰한다.
- staging과 상주 글꼴 사이에 overflow guard를 두고 로더 후 변화를 검사한다.
- 35 sector payload 전체를 예약하므로 마지막 1,180바이트 padding도 RAM 범위 안에 둔다.

## 8. 빌드 절차

1. 교차 시험으로 staging 방식이 입증된 뒤에만 ROM 빌드를 허용한다.
2. `build_menu_glyph_poc.py`로 같은 `current.bin`을 PLAN-004 기준 상태로 재구성한다.
3. 전체 글꼴 빌더에 staging 예약·읽기·CPU 복사 루프를 반영한다.
4. 기존 조기 로더 코드를 교체하고 조회 훅은 성공 상태에서만 RAM 글꼴을 사용하도록 유지한다.
5. `DUMMY.DUM` extent, 디스크 크기와 CUE를 유지한다.
6. 수정한 Mode 2 Form 1 sector의 EDC와 P/Q ECC를 재계산한다.
7. 전체 diff가 manifest의 실행 파일과 35개 글꼴 sector를 벗어나지 않는지 검사한다.
8. 원자 교체 뒤 임시 전체 ROM을 제거하고 BIN 한 개만 남긴다.

## 9. 검증 절차

### 정적·격리 검증

- staging과 상주 영역의 주소·크기·guard를 검사한다.
- 35회 읽기 인자와 2,048바이트 복사 목적지를 전수 검사한다.
- 첫·중간·마지막 sector와 전체 payload를 격리 실행으로 비교한다.
- 상태별 로더 경로, magic 검사, 2,350자 조회와 BIOS fallback을 실행한다.
- load delay, delay slot, 저장 레지스터, stack과 copy 경계를 검사한다.
- EDC/ECC, ISO 구조, ROM 크기와 diff manifest를 검사한다.

### 일반 BIOS 런타임 검증

1. 35개 글꼴 sector가 각각 staging buffer에 정확히 도착하는지 확인한다.
2. 각 CPU 복사 뒤 상주 sector의 SHA-256을 디스크 payload와 비교한다.
3. 최종 71,680바이트 payload와 70,500바이트 글꼴 해시를 비교한다.
4. `FQ4F` trailer, guard와 `font_ready=1`을 확인한다.
5. 실제 조회 훅에서 첫·마지막 글자와 PLAN-004 13자가 올바른 RAM 주소를 반환하는지 확인한다.
6. 변환기와 `LoadImage`가 RAM 글리프를 소비하는지 기록한다.
7. 일반 BIOS 화면에서 `교섭중`, `시간경과`, `부대이동`, `탐색`을 확인한다.
8. 타이틀·지도·전투·지역 이동·메뉴 반복·세이브 로드·soft reset 뒤 글꼴 해시와 guard를 검사한다.
9. XA와 다른 게임 파일 읽기가 정상인지 확인한다.

화면 자동 확인이 불가능하면 RAM 해시와 실제 GPU 업로드까지 기술 검증하고 화면은 사용자 확인 항목으로 분리한다.

## 10. 판정 기준

### 통과

1. 교차 시험으로 실패 조건이 주소 또는 sector 조건 중 하나로 분리된다.
2. 안전한 2,048바이트 staging buffer의 소유권과 수명이 확인된다.
3. 35개 sector와 전체 RAM payload 해시가 디스크와 일치한다.
4. `font_ready=1`, guard, 2,350자 조회와 BIOS fallback이 정상이다.
5. 실제 변환기와 GPU가 RAM 글리프를 소비한다.
6. 일반 BIOS 화면에서 확인 문자열이 정상 표시된다.
7. 게임 진행, CD/XA, 세이브 로드와 reset이 유지된다.
8. EDC/ECC, ISO, diff, 입력 보존과 BIN 한 개 조건을 통과한다.

### 부분 통과

RAM payload와 실제 GPU 업로드는 통과했지만 사용자 화면 확인 또는 장시간 회귀가 남으면 부분 통과로 기록한다.

### 실패

낮은 staging buffer에서도 글꼴 sector를 읽지 못하거나 안전한 buffer를 확보하지 못하고, CPU 복사 후 해시가 다르거나 게임 메모리·CD 동작이 손상되면 실패로 기록한다. 최초 실패 경계와 다음 대안을 완료 문서에 남긴다.

## 11. 산출물

- `tools/scripts/`: 교차 시험, staging 로더 빌드와 검증 스크립트
- `docs/fq4/analysis/009/README.md`: 재현 방법과 한계
- `docs/fq4/analysis/009/cross-read-tests.json`: 네 가지 주소·sector 교차 시험
- `docs/fq4/analysis/009/staging-buffer.json`: 후보와 소유권·수명 근거
- `docs/fq4/analysis/009/build-manifest.json`: 코드·RAM·sector 변경 내역
- `docs/fq4/analysis/009/verification.json`: 격리·ROM·런타임 결과
- `work/fq4/009/`: 최소 로그, RAM sample과 화면 자료
- `docs/fq4/finish/009-low-memory-font-staging-loader.md`: 완료 문서

## 12. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: 주소·sector 교차 시험, staging buffer 선정, sector별 CPU 복사 로더 구현과 일반 BIOS 검증
- ROM 쓰기 조건: 낮은 staging buffer에서 글꼴 sector가 정확히 읽히고 buffer 수명이 확인된 뒤에만 수행
