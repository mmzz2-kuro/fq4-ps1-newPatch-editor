# FQ4-PLAN-008 — 인터럽트 활성화 이후 글꼴 로더 이관 계획

- 작성일: 2026-09-13
- 상태: **실행 완료 — 부분 실패**
- 선행 결과: [FQ4-FINISH-007](../finish/007-cd-dma-font-load-fix.md)
- 작업 ROM: `work/fq4/rom/current.bin` 한 벌
- 시작 SHA-256: `5f51ea36e4118f9dd0af2cc0879c50ccea6066e39ba2dcbd40f19bdbbcff620f`
- 완료 문서 예정: `docs/fq4/finish/008-deferred-font-loader-hook.md`

## 1. 목적

현재 malloc 직후 실행되는 전체 글꼴 로더를 CD 데이터 interrupt가 정상 처리되는 이후 시점으로 옮긴다. 기존 게임의 성공한 CD 읽기 호출을 기준으로 안전한 실행 문맥을 찾고, 글꼴을 한 번만 적재하는 지연 초기화 훅을 구현한다.

성공 조건은 raw LBA `24184..24218`의 35개 sector가 예약 RAM에 정확히 기록되고 `font_ready=1`이 되며, 일반 BIOS에서 한글 글리프가 실제 렌더러와 GPU 업로드 경로에 도달하는 것이다.

## 2. 현재 실패 경계

- 디스크 payload, LBA, 전체 글꼴과 EDC/ECC는 정상이다.
- 게임 CD wrapper `0x8008F600`의 인자는 `(목적지, ISO 논리 LBA, sector 수)`이다.
- raw LBA 24184에 대응하는 wrapper 입력은 논리 LBA 24034이다.
- 현재 malloc 직후 호출하면 올바른 위치로 seek하지만 `Data interrupt was not delivered`가 반복된다.
- 해당 시점에서는 CD interrupt 처리 문맥이 준비되지 않아 RAM DMA가 발생하지 않는다.
- 실패 시 `font_ready=0`과 BIOS fallback이 유지된다.

## 3. 승인 범위

- 게임 부팅 중 CD interrupt가 활성화되는 정확한 지점을 찾는다.
- 정상적으로 완료되는 기존 `0x8008F600` 호출들의 호출자, 시점과 반환 상태를 추적한다.
- 글꼴 조회가 처음 발생하기 전이면서 CD가 유휴 상태인 안전한 훅 후보를 비교한다.
- 로더를 한 번만 실행하는 상태 기계와 재진입 방지를 설계한다.
- 필요하면 글꼴 조회 시 적재를 예약하고 다음 안전한 main-loop 지점에서 실행하는 2단계 구조를 사용한다.
- 원인이 검증된 뒤 같은 `current.bin`을 PLAN-004 기준으로 재구성하고 수정본을 적용한다.
- 정적·격리·일반 BIOS 런타임과 화면 표시를 검증한다.
- 결과를 완료 문서에 기록한다.

배포용 xdelta, 사용자 GUI, 번역문 변경과 실기 최종 검증은 포함하지 않는다.

## 4. 보존 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 수정·이동·삭제하지 않는다.
- 전체 ROM은 `work/fq4/rom/current.bin` 하나만 유지한다.
- 새 BIN·ISO·IMG 또는 보존용 ROM 복사본을 만들지 않는다.
- 재빌드는 같은 ROM을 PLAN-004 상태로 복원한 다음 수정된 전체 글꼴 구현을 적용한다.
- 쓰기 전 입력 해시, 훅 원본 명령과 모든 변경 범위를 검사한다.
- 분석·변환·빌드·검증 스크립트는 `tools/scripts/`에 둔다.
- 추적 로그와 작은 RAM sample만 `work/fq4/008/`에 보존한다.

## 5. 조사 절차

### A. 정상 CD 읽기 호출 추적

1. `0x8008F600` 및 하위 `CdRead`·동기화 wrapper에 breakpoint를 설정한다.
2. 부팅부터 타이틀과 지도 화면까지 각 호출의 `PC`, `RA`, `a0..a2`, stack과 반환값을 기록한다.
3. DuckStation 로그에서 각 호출의 Setloc, ReadN, data interrupt, DMA와 Pause 완료를 연결한다.
4. 성공 호출과 현재 글꼴 호출의 interrupt mask, DMA channel 3, CD callback 전역 상태를 비교한다.
5. 최초 성공 호출 이전과 이후의 초기화 함수를 역추적해 interrupt 활성화 경계를 확정한다.

### B. 훅 후보 선정

후보마다 다음 조건을 검사한다.

- interrupt가 활성화되어 CD data interrupt와 DMA가 정상 완료된다.
- 글꼴이 필요한 최초 화면보다 먼저 실행된다.
- 기존 CD/XA 읽기와 중첩되지 않거나 종료를 확인할 수 있다.
- 전투·지도·세이브 로드 중 반복 호출되더라도 일회성 guard가 작동한다.
- 호출자 ABI와 원래 동작을 보존할 수 있다.
- 실행 파일의 제품용 코드 영역 안에서 구현 가능하다.

우선순위는 초기화 완료 직후의 단일 main-loop 진입점, 최초 정상 파일 읽기 직후, 반복 main-loop의 guarded 호출 순이다. 렌더러 내부에서 35개 sector를 동기식으로 읽는 방식은 화면 중단과 재진입 위험 때문에 마지막 후보로만 검토한다.

### C. 일회성 상태 기계

다음 상태를 사용한다.

| 값 | 의미 |
|---|---|
| `0` | 아직 시도하지 않음 |
| `1` | 적재 진행 중 |
| `2` | 적재 및 magic 검증 성공 |
| `3` | 적재 실패, BIOS fallback 고정 |

1. 안전 훅은 상태 0에서만 1로 전환하고 로더를 호출한다.
2. CD wrapper 성공과 `FQ4F` magic을 모두 확인하면 상태 2로 전환한다.
3. 오류가 발생하면 상태 3으로 바꾸고 같은 세션에서 무한 재시도하지 않는다.
4. 조회 훅은 상태 2일 때만 RAM 글꼴을 반환한다.
5. soft reset과 새 부팅에서는 실행 파일 데이터 초기화에 따라 상태 0에서 다시 시작한다.

### D. RAM 수명 재검증

- 지연 적재 시점에도 주 메모리 풀 상단 예약 주소가 유효한지 확인한다.
- 적재 전후 allocator의 최대 주소가 글꼴 영역에 닿지 않는지 감시한다.
- 지도·전투·메뉴·세이브 로드 이후 글꼴 해시가 유지되는지 반복 측정한다.
- 필요하면 guard와 글꼴 포인터를 기존보다 명확한 전역 데이터 영역으로 옮긴다.

## 6. 구현 절차

1. 기존 malloc 직후 로더 호출을 제거하고 원래 pool 초기화 호출을 복원한다.
2. pool 크기 감소와 `font_base` 계산은 메모리 풀 초기화 전에 유지한다.
3. 선정된 안전 훅에 원래 명령을 보존하는 trampoline을 설치한다.
4. trampoline에서 상태 0일 때만 지연 로더를 실행하고 원래 흐름으로 복귀한다.
5. 로더는 `0x8008F600(font_base, 24034, 35)`을 사용한다.
6. 성공 후 RAM trailer의 `FQ4F`를 검사해 상태 2를 기록한다.
7. 조회 훅은 상태 2이면 2,350자 산술 주소를, 나머지는 BIOS `B0(51h)`를 반환한다.
8. 코드와 전역은 PLAN-006에서 사용한 실행 파일 내부 영역을 재감사한 후 배치한다.

## 7. 재빌드와 무결성 검사

1. 같은 `current.bin`을 PLAN-004 기준 SHA-256 `1911cfe9d9ca963a2761414c5df0881115759628ffdea637c97f8dbf62da3b86`으로 재구성한다.
2. 수정된 전체 글꼴 빌더를 한 번 적용한다.
3. `DUMMY.DUM` extent, ISO 디렉터리, ROM 크기와 CUE를 유지한다.
4. 수정한 모든 Mode 2 Form 1 sector의 EDC와 P/Q ECC를 재계산한다.
5. 전체 diff가 manifest의 실행 파일 및 35개 글꼴 sector 범위를 벗어나지 않는지 확인한다.
6. 임시 전체 ROM은 원자 교체 직후 제거하고 BIN 한 개만 남긴다.

## 8. 검증 절차

### 정적·격리 검증

- trampoline이 덮은 원래 명령과 ABI를 정확히 재현하는지 검사한다.
- 상태 0·1·2·3과 성공·오류·재진입 경로를 격리 실행한다.
- 로더가 세션당 한 번만 호출되는지 검사한다.
- 전체 2,350자 주소, 상태별 BIOS fallback과 비한글 코드를 전수 검사한다.
- load delay, branch/jump delay slot, stack과 저장 레지스터를 검사한다.
- payload, EDC/ECC, ISO 구조와 전체 ROM diff를 검사한다.

### 일반 BIOS 런타임 검증

1. cold boot에서 이전 위치의 조기 CD 호출이 사라졌는지 확인한다.
2. 안전 훅 진입 시 interrupt 및 CD 유휴 상태를 기록한다.
3. LBA `24184..24218`이 한 번 읽히고 data interrupt·DMA가 정상 처리되는지 확인한다.
4. 상태가 `0→1→2`로 변하고 로더 호출 횟수가 1인지 확인한다.
5. RAM 글꼴 SHA-256이 `7d49b80781a274ebd0b83abcff87889c9081be7a3a3e9139b2314414ab520a84`와 일치해야 한다.
6. 실제 조회 훅, 변환기와 `LoadImage`가 RAM 글리프를 소비하는지 기록한다.
7. `교섭중`, `시간경과`, `부대이동`, `탐색`을 일반 BIOS 화면에서 확인한다.
8. 타이틀·지도·전투·지역 이동·세이브 로드·soft reset 뒤 상태와 글꼴 해시를 검사한다.
9. 기존 XA 재생과 다른 파일 읽기가 정상인지 확인한다.

화면 자동 확인이 불가능하면 RAM 해시와 실제 GPU 업로드까지 기술 검증하고 최종 화면은 사용자 확인 항목으로 남긴다.

## 9. 판정 기준

### 통과

1. 정상 CD interrupt가 가능한 호출 경계가 정적·런타임 근거로 확정된다.
2. 글꼴 로더가 한 번 실행되고 상태 2가 된다.
3. 디스크와 RAM의 전체 글꼴 해시가 일치한다.
4. 2,350자 조회와 BIOS fallback이 정상이다.
5. 실제 렌더러와 GPU가 RAM 글리프를 소비한다.
6. 일반 BIOS 화면에서 확인 문자열이 정상 표시된다.
7. CD/XA, 전투·이동·세이브 로드·reset이 유지된다.
8. EDC/ECC, ISO, diff, 입력 보존과 BIN 한 개 조건을 통과한다.

### 부분 통과

RAM 해시와 실제 GPU 업로드는 통과했지만 사용자 화면 확인 또는 장시간 회귀가 남으면 부분 통과로 기록한다.

### 실패

안전한 훅 지점을 찾지 못하거나 CD interrupt 오류가 계속되고, RAM 해시·게임 진행·기존 CD/XA 또는 ROM 무결성이 손상되면 실패로 기록한다. 실패 시 현재 검증 가능한 상태와 다음 대안을 완료 문서에 남긴다.

## 10. 산출물

- `tools/scripts/`: 정상 CD 호출 추적, 지연 로더 빌드와 검증 스크립트
- `docs/fq4/analysis/008/README.md`: 재현 방법과 한계
- `docs/fq4/analysis/008/cd-interrupt-boundary.json`: 성공 호출과 활성화 경계
- `docs/fq4/analysis/008/hook-candidates.json`: 후보 비교와 선정 근거
- `docs/fq4/analysis/008/build-manifest.json`: 코드·데이터·sector 변경 내역
- `docs/fq4/analysis/008/verification.json`: 격리·ROM·런타임 결과
- `work/fq4/008/`: 최소 추적 로그와 화면 자료
- `docs/fq4/finish/008-deferred-font-loader-hook.md`: 완료 문서

## 11. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: 정상 CD interrupt 경계 추적, 안전 훅 선정, 일회성 지연 로더 구현과 일반 BIOS 검증
- ROM 쓰기 조건: 훅 후보가 실제 정상 CD 호출과 같은 interrupt 문맥임을 확인하고 격리 검사를 통과한 뒤에만 수행
