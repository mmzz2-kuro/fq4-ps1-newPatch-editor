# FQ4-FINISH-007 CD DMA 글꼴 적재 실패 추적

- 완료일: 2026-09-13
- 결과: **부분 실패 — ABI·LBA 확정, 호출 시점 부적합 확인**
- 계획: [PLAN-007](../plans/007-cd-dma-font-load-fix.md)

## 결과

RAM 2MB에서 글꼴 sector fingerprint를 검색했으나 하나도 발견되지 않았다. 정상 게임 CD wrapper `0x8008F600`의 ABI는 `(목적지, ISO 논리 LBA, sector 수)`로 확정했고 raw LBA 24184를 위해 논리 LBA 24034를 사용하도록 고쳤다.

격리 검사는 pool 예약, 전체 payload, 2,350자 조회, fallback과 38개 sector EDC/ECC를 통과했다. 실제 일반 BIOS에서도 `Setloc 05:22:34`와 raw LBA 24184 접근까지 확인됐다.

하지만 현재 malloc 직후 주입 지점에서는 `Pause Seeking => Error`와 `Data interrupt was not delivered`가 반복됐다. CD 데이터 interrupt가 처리되지 않아 RAM은 변하지 않았고 `font_ready=0`으로 남았다. 주소나 글꼴 데이터 문제가 아니라 호출 문맥 문제로 판정한다.

## 현재 ROM

- SHA-256: `5f51ea36e4118f9dd0af2cc0879c50ccea6066e39ba2dcbd40f19bdbbcff620f`
- BIN 수: 1
- 이 실험본은 안전 fallback으로 부팅하지만 일반 BIOS 한글 표시는 아직 되지 않는다.
- 보호된 원본·패치·BIOS는 수정하지 않았다.

## 다음 단계

기존 게임의 정상 CD 읽기가 성공하는 호출 시점과 interrupt 활성화 상태를 추적해야 한다. 로더를 해당 시점에 한 번만 실행하도록 옮긴 뒤 RAM 해시, 실제 글리프 조회와 화면을 다시 검증한다.
