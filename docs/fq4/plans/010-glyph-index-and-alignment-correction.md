# FQ4-PLAN-010 — 전체 한글 글리프 위치 교정 계획

- 작성일: 2026-09-13
- 상태: **사용자 확인 대기**
- 선행 결과: [FQ4-FINISH-009](../finish/009-low-memory-font-staging-loader.md)
- 시작 ROM: `work/fq4/rom/current.bin`
- 시작 SHA-256: `123b2356a444139f1b874685b9f7f8ddc2f1101d07e2dedb013cefd1449e0937`
- 완료 문서 예정: `docs/fq4/finish/010-glyph-index-and-alignment-correction.md`

## 1. 증상과 목적

일반 BIOS에서 전체 한글 글꼴 적재에는 성공했지만 지도 메뉴의 한글 획이 조금씩 밀리고 깨진 것처럼 표시된다. 화면상 각 칸에는 한글 형태가 남아 있으므로 CD 적재 실패보다는 조회 포인터의 시작 위치, 글리프 stride, 행 단위 byte 해석 또는 문자 코드→글리프 인덱스 변환의 오차를 우선 의심한다.

실제 메뉴 문자열의 입력 코드, 반환 포인터, 30바이트 원본 글리프와 GPU 변환 결과를 한 글자씩 연결해 최초 오차 지점을 찾고 전체 2,350자 조회를 교정한다.

## 2. 승인 범위

- 화면에 나온 `시간경과`, `부대이동`, `탐색`의 실제 2바이트 코드와 런타임 반환 주소를 수집한다.
- PLAN-004에서 정상 표시된 13자 개별 매핑을 정답 기준으로 사용한다.
- 같은 코드에 대해 기존 BIOS syscall 반환 주소, 개별 PoC 주소, 현재 산술 조회 주소를 비교한다.
- 글리프 시작 offset, 30바이트 stride, 2바이트 정렬과 행별 bit 순서를 비교한다.
- 문자 코드→JIS 행/셀→KS X 1001 인덱스 변환식과 MIPS 구현을 독립 계산 결과와 대조한다.
- 원인을 확정한 뒤 현재 전체 글꼴 조회 훅만 최소 수정한다.
- 일반 BIOS에서 대표 문자열과 첫·중간·마지막 글리프를 다시 검증한다.

번역문, 디스크 글꼴 payload, CD 로더 구조, GUI와 배포용 xdelta 생성은 포함하지 않는다.

## 3. 보존 및 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 읽기 전용이다.
- 전체 ROM은 `work/fq4/rom/current.bin` 한 개만 유지한다.
- 시험용 전체 BIN·ISO·IMG를 추가 생성하지 않는다.
- 비교가 필요하면 현재 ROM을 PLAN-004 또는 PLAN-009 상태로 같은 파일에 재현한다.
- 분석·변환·검증 코드는 `tools/scripts/`에 작성한다.
- 작은 글리프 sample, 주소, 해시와 로그만 `work/fq4/010/`에 저장한다.

## 4. 진단 절차

### A. 정상 기준표 작성

PLAN-004에서 정상 표시가 확인된 13자에 대해 다음 항목을 표로 만든다.

- 완성형 문자와 게임의 2바이트 코드
- 한글 BIOS 내부 offset
- 개별 PoC에서 사용한 30바이트 글리프 해시
- KS X 1001 행·열 및 기대 dense index
- 현재 산술 조회가 반환하는 index와 RAM 주소

13자 모두에서 일정한 `+N/-N byte`가 나타나면 base offset 오류로, 글자마다 차이가 증가하면 stride 또는 행·열 계산 오류로 판정한다.

### B. 런타임 경로 추적

일반 BIOS cold boot에서 실제 조회 훅 `0x80082C8C`을 추적한다. 대표 문자열의 각 코드마다 반환 포인터의 앞뒤 4바이트를 포함한 38바이트만 읽고 다음을 비교한다.

1. RAM payload의 기대 30바이트
2. 한글 BIOS의 정답 30바이트
3. 변환 함수가 읽은 15개 행
4. GPU `LoadImage` 직전의 변환 결과

이 과정으로 조회 주소가 틀린지, 주소는 맞지만 소비 함수가 RAM 정렬에 따라 다르게 읽는지 분리한다.

### C. 변환식 전수 검사

- 게임에서 쓰는 코드 domain을 실제 문자열과 PLAN-004 매핑으로 확정한다.
- Shift-JIS lead/trail 변환의 `0x7F` hole과 `0x9F` 행 전환 경계를 검사한다.
- KS X 1001 `0xB0A1..0xC8FE` 순서와 BIOS 연속 글리프 순서를 비교한다.
- Python 기준 구현과 MIPS lookup을 2,350개 코드에 대해 주소 단위로 비교한다.
- 첫 글자, 각 94자 행 경계, 마지막 글자에서 기대 BIOS offset까지 비교한다.

## 5. 수정 후보와 선택 기준

원인이 확인된 한 항목만 적용한다.

1. **base offset 오류:** 상주 글꼴 시작 주소 또는 payload 추출 시작 offset을 교정한다.
2. **stride 오류:** 실제 BIOS 글리프 간격에 맞춰 주소 계산을 교정한다.
3. **인덱스 변환 오류:** JIS 행·셀 또는 KS dense index 계산을 교정한다.
4. **RAM 정렬 의존:** 조회 결과를 원본 BIOS와 같은 halfword 정렬로 보장하고 소비 함수의 unaligned load를 교정한다.
5. **행 bit 해석 오류:** RAM 경로에서만 달라진 endian/bit shift를 변환 단계에서 교정한다.

화면만 보고 여러 보정을 동시에 넣지 않는다. 정답 글리프 13자의 byte 비교로 원인을 확정한 뒤 최소 변경을 선택한다.

## 6. 빌드 및 검증

1. `current.bin`을 PLAN-009 빌드 절차로 같은 파일에 재현한다.
2. 입력 SHA, 기존 훅 명령과 글꼴 payload 해시를 확인한다.
3. 확정된 조회 또는 변환 코드만 수정한다.
4. 수정한 실행 파일 sector의 EDC와 P/Q ECC를 재계산한다.
5. 전체 diff가 실행 파일의 등록된 sector와 기존 35개 글꼴 sector 밖으로 확장되지 않았는지 검사한다.
6. 2,350개 코드의 기대 포인터와 30바이트 글리프 해시를 전수 검사한다.
7. 일반 BIOS에서 RAM 전체 글꼴 해시와 `font_ready=1`을 다시 확인한다.
8. `시간경과`, `부대이동`, `탐색`의 실제 조회와 GPU 업로드를 확인한다.
9. 사용자에게 같은 메뉴 화면의 최종 육안 확인을 요청한다.

## 7. 통과 기준

- PLAN-004의 정답 13자가 모두 같은 30바이트 글리프를 반환한다.
- 2,350개 코드가 BIOS의 대응 글리프와 byte 단위로 일치한다.
- 행 경계와 정렬이 다른 글리프에서도 밀림이나 획 손실이 없다.
- 일반 BIOS에서 글꼴 payload 해시, trailer와 `font_ready=1`이 유지된다.
- 대표 메뉴 문자열의 조회 결과와 GPU 입력이 기대값과 일치한다.
- 사용자 화면에서 대표 문자열이 정상 표시된다.
- ISO, EDC/ECC, CD 동작과 작업 ROM 한 개 조건을 유지한다.

기술 검증은 통과했으나 최종 화면 확인만 남으면 부분 통과로 기록한다.

## 8. 산출물

- `tools/scripts/`: 글리프 주소 대조, 런타임 추적, 교정 빌드 및 검증 스크립트
- `docs/fq4/analysis/010/reference-glyphs.json`: 정상 13자 기준표
- `docs/fq4/analysis/010/runtime-glyph-trace.json`: 코드→주소→변환→GPU 추적
- `docs/fq4/analysis/010/lookup-verification.json`: 2,350자 전수 비교
- `docs/fq4/analysis/010/build-manifest.json`: 변경 범위와 해시
- `docs/fq4/analysis/010/README.md`: 원인, 재현법과 한계
- `docs/fq4/finish/010-glyph-index-and-alignment-correction.md`: 완료 문서

## 9. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: 정상 13자 byte 대조, 런타임 조회·변환 추적, 원인별 최소 교정, 전체 조회와 일반 BIOS 재검증
- ROM 쓰기 조건: 정답 글리프 대조로 오차 유형을 확정한 뒤에만 적용
