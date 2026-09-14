# FQ4-FINISH-008 인터럽트 활성화 이후 글꼴 로더 조사

- 완료일: 2026-09-13
- 결과: **부분 실패 — 인터럽트 가설 기각, 목적지 RAM 제약으로 경계 이동**
- 계획: [PLAN-008](../plans/008-deferred-font-loader-hook.md)

## 확정 결과

정상 CD wrapper `0x8008F600`의 실제 ABI는 `(sector 수, ISO 논리 LBA, RAM 목적지)`이다. 글꼴 호출을 `(1, 24034..24068, 0x801E6528부터 0x800씩 증가)`로 수정했다. 35개 sector는 모두 정확한 raw LBA `24184..24218`에서 오류 없이 읽혔고 이전의 `Data interrupt was not delivered`도 사라졌다.

따라서 로더 호출 시점과 interrupt 문맥은 사용할 수 있다. 지연 훅 이관은 필요하지 않다고 판정했다.

하지만 CD 반환 직후에도 높은 heap 목적지의 글꼴 해시는 일치하지 않았고 `font_ready=0`이었다. 정상 PVD 읽기는 같은 wrapper로 낮은 고정 버퍼 `0x801179BC`에 올바른 데이터를 남겼다. 남은 최초 실패 경계는 SDK의 목적지 RAM 처리 또는 내부 staging/bounce buffer 제약이다.

35개 sector payload 예약량도 70,656바이트에서 실제 sector payload 크기인 71,680바이트로 수정했다.

## 검증 상태

- 게임 CD wrapper 실제 인자: 통과
- raw LBA와 35회 sector 완료: 통과
- data interrupt 오류 제거: 통과
- 전체 글꼴 정적 payload·EDC/ECC: 통과
- 2,350자 격리 조회 및 fallback: 통과
- 런타임 RAM 글꼴 해시: 실패
- 일반 BIOS 한글 화면: 미도달

## 현재 ROM

- SHA-256: `b3000a9795faf1851af261732bc61208be7d76a0ddaf3a9fa118225a458fb241`
- 전체 BIN: 1개
- magic 실패 시 BIOS fallback을 사용하므로 일반 BIOS 한글은 아직 표시되지 않는다.
- 보호된 원본·패치·BIOS는 수정하지 않았다.

## 다음 단계

검증된 낮은 버퍼와 높은 글꼴 주소를 교차 시험한다. PVD를 높은 주소로 읽고 글꼴 sector를 `0x801179BC`로 읽어 주소와 sector 중 어느 조건이 실패를 만드는지 분리한다. 낮은 staging buffer에서 글꼴 sector가 확인되면 1-sector씩 `font_base`로 복사하는 제품 로더를 설계한다.
