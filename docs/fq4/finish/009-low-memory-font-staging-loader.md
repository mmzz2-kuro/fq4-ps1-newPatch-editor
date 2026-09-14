# FQ4-FINISH-009 글꼴 로더 sector 보정 수정

- 완료일: 2026-09-13
- 결과: **기술 검증 통과, 사용자 화면 확인 대기**
- 계획: [PLAN-009](../plans/009-low-memory-font-staging-loader.md)
- 분석: [analysis/009](../analysis/009/README.md)

## 결과

교차 시험 결과 낮은 staging buffer와 CPU 복사는 필요하지 않았다. PVD sector 16은 낮은 주소 `0x801179BC`와 높은 주소 `0x801E6528`에서 같은 데이터로 읽혔다. 반면 기존 글꼴 요청값 24034는 어느 주소에서도 글꼴이 아닌 BIN sector 24034를 반환했다.

`GAME_CD_READ`가 내부 MSF 변환에서 lead-in 150 frame을 이미 더하므로 DUMMY.DUM의 BIN sector 24184를 그대로 전달해야 한다. 로더 시작값을 `24034 (0x5DE2)`에서 `24184 (0x5E78)`로 수정했다.

## 검증

- 일반 BIOS cold boot: 통과
- 런타임 글꼴 주소: `0x801E6528`
- `font_ready`: `1`
- 글꼴 70,500바이트 SHA-256: `7d49b80781a274ebd0b83abcff87889c9081be7a3a3e9139b2314414ab520a84`
- trailer: `FQ4F`, version 1, 2,350자, 70,500바이트
- 2,350개 조회 격리 검증: 통과
- Mode 2 Form 1 EDC/ECC 38개 변경 sector: 통과
- ISO 파일 398개와 DUMMY.DUM extent: 유지
- 작업 ROM BIN 개수: 1개

실제 화면에서 메뉴 문자열을 확인하는 사용자 플레이 테스트는 남아 있다. 로더와 전체 글꼴 데이터가 일반 BIOS RAM에 정상 상주하는 지점까지는 확인했다.

## 현재 작업 ROM

- 파일: `work/fq4/rom/current.bin`
- SHA-256: `123b2356a444139f1b874685b9f7f8ddc2f1101d07e2dedb013cefd1449e0937`
- 크기: 101,140,704바이트

`original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않았다. 전체 작업 ROM은 기존 `current.bin` 한 벌만 유지했다.
