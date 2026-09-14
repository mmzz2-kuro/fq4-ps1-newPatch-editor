# FQ4-PLAN-007 — CD DMA 글꼴 적재 실패 추적 및 수정 계획

- 작성일: 2026-09-13
- 상태: **실행 완료 — 부분 실패**
- 선행 결과: [FQ4-FINISH-006](../finish/006-full-font-runtime-implementation.md)
- 작업 ROM: `work/fq4/rom/current.bin` 한 벌
- 시작 SHA-256: `9e409a57035e693f8e8a3da0a4ee69100d5d8011aeb29c600a381cf2add3d055`
- 완료 문서 예정: `docs/fq4/finish/007-cd-dma-font-load-fix.md`

## 1. 목적

PLAN-006에서 `DUMMY.DUM`의 LBA `24184..24218` 읽기는 확인됐지만 예약 RAM의 글꼴 해시와 trailer가 일치하지 않아 `font_ready`가 설정되지 않았다. 이번 단계에서는 PsyQ `CdRead` 호출 전후의 DMA 주소, 전송 크기, sector별 RAM 배치와 완료 상태를 측정해 원인을 확정한다.

원인이 확인되면 로더를 최소 범위로 수정하고 동일한 `current.bin` 한 벌을 다시 빌드한다. RAM의 70,500바이트가 원본 글꼴과 일치하고 일반 BIOS에서 실제 렌더링되는 데까지 검증한다.

## 2. 현재 확인된 사실

- `CdControl(2, 05:22:34, 0)`은 LBA 24184를 가리킨다.
- DuckStation에서 LBA `24184..24218`의 35개 sector 읽기가 관찰됐다.
- 디스크 payload와 한글 BIOS 글리프 영역은 일치한다.
- 격리 실행에서는 pool 예약, magic 검사와 2,350자 조회가 통과했다.
- 실제 실행은 `font_base=0x801E6928`, `font_ready=0`이다.
- 실제 RAM 해시는 `9e715fb475f286aa4a3d4a5f329f9ad310ce4abedcfb68c6a76aa60f98175cbd`로 기대값과 다르며 trailer도 0이다.
- magic 실패 시 BIOS fallback을 사용하므로 현재 실험 ROM은 한글을 표시하지 않는다.

## 3. 승인 범위

- `CdRead`와 CD DMA 관련 전역 상태·콜백을 정적 분석한다.
- 실제 실행에서 로더 전후 RAM과 CD 함수 인자를 읽는다.
- 예약 영역 주변에서 각 글꼴 sector의 고유 패턴을 찾아 실제 기록 주소, 간격, 순서, 누락과 중복을 측정한다.
- `CdRead`의 buffer 단위, mode, alignment와 `CdReadSync` 완료 조건을 정상 게임 호출부와 비교해 확정한다.
- 덮어쓰기, 캐시 alias 또는 기존 CD/XA 상태 충돌 여부를 조사한다.
- 원인이 확정되면 필요한 로더 변경만 적용한다.
- 같은 작업 ROM을 PLAN-004 상태에서 재구성한 뒤 수정된 전체 글꼴 구현을 한 번 적용한다.
- EDC/ECC, ISO, MIPS 격리 실행과 일반 BIOS 런타임을 다시 검증한다.
- 결과를 완료 문서에 기록한다.

번역문 변경, 배포용 xdelta, GUI 및 실기 최종 검증은 포함하지 않는다.

## 4. 보존 및 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 모든 BIOS는 읽기 전용이다.
- 전체 ROM은 `work/fq4/rom/current.bin` 하나만 유지한다.
- 새 BIN·ISO·IMG나 보존용 ROM 복사본을 만들지 않는다.
- 재빌드는 기존 스크립트가 같은 `current.bin`을 PLAN-004 기준으로 되돌린 뒤 한 번 덮어쓰는 방식으로 수행한다.
- 빌더는 입력 해시와 예상 바이트를 검사하고 임시 파일을 즉시 원자 교체한다.
- 분석·변환·빌드 스크립트는 `tools/scripts/`에 둔다. 사용자용 GUI는 만들지 않는다.
- RAM dump는 전체 2MB를 반복 보관하지 않고 필요한 범위의 해시, 검색 위치와 작은 sample만 `work/fq4/007/`에 남긴다.

## 5. 조사 절차

### A. 시작 상태 재검증

1. 현재 ROM, 보호 입력, BIOS와 CUE의 해시를 확인한다.
2. `DUMMY.DUM`의 35개 payload와 EDC/ECC를 검사한다.
3. 실행 파일의 로더, 조회 훅, 전역 주소와 호출 지점을 manifest와 비교한다.
4. cold boot에서 LBA 범위와 `font_ready=0`을 한 번 재현한다.

시작 상태가 기록과 다르면 ROM을 수정하지 않고 차이를 먼저 문서화한다.

### B. 실제 RAM 기록 위치 추적

1. `CdRead` 직전 예약 영역과 주변 RAM의 fingerprint를 기록한다.
2. 완료 직후 RAM에서 첫·중간·마지막 sector의 고유 32~64바이트 패턴을 검색한다.
3. 발견 주소가 `font_base`, sector offset, word 주소 변환 또는 uncached alias와 어떤 관계인지 계산한다.
4. 35개 sector의 시작 패턴을 찾아 간격, 순서, 중복과 누락을 기록한다.
5. 패턴이 없으면 DMA channel 3 상태와 CD data FIFO 소비 경로를 추적한다.
6. 이후 초기화가 글꼴 영역을 덮는지 시간차를 두고 비교한다.

GDB 정지가 타이밍을 바꾸는 경우 breakpoint를 최소화하고 DuckStation CD/DMA 로그와 사후 RAM 검사를 분리한다.

### C. PsyQ CD 함수 ABI 확정

1. `CdRead(0x8008E1FC)`가 인자를 저장하는 전역과 DMA setup 함수까지 역추적한다.
2. 게임의 정상 `CdRead` 호출부에서 sector 수, buffer 주소와 mode 값을 수집한다.
3. `CdReadSync(0x8008E5AC)`의 mode별 반환값과 완료 조건을 정상 호출부와 비교한다.
4. 중복 Setloc·Pause와 첫 sector 재시작의 의미를 확인한다.
5. 정렬, cache flush 또는 uncached alias 요구사항을 기존 호출 경로에서 확인한다.

함수 이름만으로 ABI를 추정하지 않고 명령열, 정상 호출부와 런타임 레지스터 중 두 가지 이상으로 확정한다.

### D. 원인 판정

다음 후보를 측정 결과로 구분한다.

- buffer가 byte pointer와 다른 단위를 요구한다.
- mode `0x80` 때문에 sector 크기나 DMA 경로가 달라진다.
- `CdReadSync(0, 0)`의 반환 시점 또는 성공 판정이 잘못됐다.
- 기존 CD/XA 상태가 새 읽기와 충돌한다.
- 예약 주소의 정렬 또는 DMA boundary가 요구 조건을 만족하지 않는다.
- 이후 메모리 초기화가 적재 데이터를 덮어쓴다.
- cache 또는 주소 alias 때문에 CPU가 DMA 결과를 보지 못한다.

최초로 입증된 원인만 수정하며 여러 추정 변경을 한 번에 적용하지 않는다.

## 6. 수정 및 재빌드

원인에 따라 buffer 주소, mode, 완료 대기, CD 상태 복구, RAM 정렬, cache 처리 또는 호출 시점 중 필요한 부분만 고친다. 성공 시에만 `font_ready=1`을 쓰고 모든 실패 경로는 BIOS fallback을 유지한다.

1. `build_menu_glyph_poc.py`로 같은 `current.bin`을 PLAN-004 상태로 재구성한다.
2. 수정한 전체 글꼴 빌더를 같은 파일에 적용한다.
3. `DUMMY.DUM` extent, 디스크 크기와 CUE를 유지한다.
4. 수정 Form 1 sector의 EDC와 P/Q ECC를 재계산한다.
5. 예상 변경 밖의 sector 또는 byte가 있으면 실패시킨다.
6. 최종 ROM 해시와 BIN 한 개 유지 상태를 기록한다.

## 7. 검증 절차

### 정적·격리 검사

- 디스크 payload와 BIOS 글꼴 해시를 비교한다.
- 로더 성공·실패 경로, pool 예약과 magic 검사를 실행한다.
- 2,350개 코드 주소와 범위 밖 BIOS fallback을 전수 검사한다.
- load delay, delay slot, ABI와 정렬을 역어셈블 검사한다.
- 수정 sector의 EDC/ECC와 전체 ROM diff를 검사한다.

### 실제 일반 BIOS 검사

1. cold boot에서 LBA `24184..24218` 읽기를 확인한다.
2. `font_ready=1`과 런타임 `font_base`를 기록한다.
3. RAM 글꼴 SHA-256이 `7d49b80781a274ebd0b83abcff87889c9081be7a3a3e9139b2314414ab520a84`와 일치해야 한다.
4. 첫·마지막 글자와 PLAN-004 13자의 RAM 바이트를 비교한다.
5. 실제 조회 훅, 변환기와 `LoadImage`가 RAM 글리프를 소비하는지 확인한다.
6. 일반 BIOS 화면에서 `교섭중`, `시간경과`, `부대이동`, `탐색`을 확인한다.
7. 타이틀, 전투, 메뉴 반복, 부대·지역 이동, 세이브·로드와 reset을 검사한다.

화면 자동 확인이 불가능하면 RAM 해시와 실제 GPU 업로드까지 기술 판정을 내리고 최종 화면은 사용자 확인 항목으로 분리한다.

## 8. 판정 기준

### 통과

1. RAM 불일치 원인이 명령열과 런타임 근거로 확정된다.
2. 수정 뒤 디스크와 RAM 글꼴 해시가 일치하고 `font_ready=1`이다.
3. 2,350자 조회와 BIOS fallback이 정상이다.
4. 실제 렌더러와 GPU 업로드가 RAM 글리프를 소비한다.
5. 일반 BIOS 화면에서 확인 문자열이 정상 표시된다.
6. CD/XA, 전투·이동·세이브·로드·reset이 유지된다.
7. EDC/ECC, ISO 구조, diff와 입력 보존 검사가 통과한다.
8. 전체 ROM은 `current.bin` 한 벌만 남는다.

### 부분 통과

RAM 해시와 실제 렌더링은 통과했지만 사용자 화면 확인 또는 장시간 회귀가 남으면 부분 통과로 기록한다.

### 실패

원인을 확정하지 못하거나 수정 뒤에도 RAM 해시가 다르고, 기존 CD/XA·부팅·게임 진행이 손상되거나 예상 밖 ROM 변경이 생기면 실패로 판정한다. 최초 실패 지점과 대안을 완료 문서에 기록한다.

## 9. 산출물

- `tools/scripts/`: RAM pattern 추적, ABI 분석, 수정 빌드와 검증 스크립트
- `docs/fq4/analysis/007/README.md`: 재현 방법과 한계
- `docs/fq4/analysis/007/ram-placement.json`: 실제 sector별 RAM 배치
- `docs/fq4/analysis/007/cd-read-abi.json`: 정상 호출부와 함수 ABI
- `docs/fq4/analysis/007/fix-manifest.json`: 원인과 최소 수정
- `docs/fq4/analysis/007/verification.json`: 정적·격리·런타임 결과
- `work/fq4/007/`: 필요한 최소 로그와 화면 자료
- `docs/fq4/finish/007-cd-dma-font-load-fix.md`: 완료 문서

## 10. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: 실패 재현, RAM·CD ABI 추적, 원인별 최소 수정, 같은 ROM 재빌드와 일반 BIOS 검증
- ROM 쓰기 조건: 원인이 측정으로 확정되고 수정안의 격리 검사가 통과한 뒤에만 수행
