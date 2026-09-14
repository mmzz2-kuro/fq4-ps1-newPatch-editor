# FQ4-FINISH-006 전체 글꼴 런타임 구현

- 완료일: 2026-09-13
- 결과: **부분 실패 — 디스크 읽기 성공, RAM 내용 검증 실패**
- 계획: [PLAN-006](../plans/006-full-font-runtime-implementation.md)

## 수행 결과

전체 2,350자 글꼴 70,500바이트를 `DUMMY.DUM`의 LBA 24184부터 35개 Form 1 섹터에 기록했다. 실행 파일에는 게임 메모리 풀 상단 70,656바이트 예약, PsyQ `CdControl`·`CdRead`·`CdReadSync` 호출, 전체 한글 산술 조회와 BIOS fallback을 구현했다.

정적 및 Unicorn 격리 검사는 통과했다. 유효 코드 2,350개의 주소, 범위 밖 fallback, pool 예약, payload, ISO 구조와 변경 38개 sector의 EDC/ECC가 모두 일치했다.

## 실제 일반 BIOS 결과

DuckStation 로그에서 최초 MSF 계산이 150 sector 뒤인 LBA 24334를 읽는 문제를 발견해 `05:22:34`로 수정했다. 재검사에서는 LBA `24184..24218` 전부가 실제로 읽혔고 이후 게임의 XA 읽기도 계속됐다.

그러나 런타임 RAM 프로브 결과는 다음과 같다.

- `font_base`: `0x801E6928`
- `font_ready`: `0`
- 기대 글꼴 SHA-256: `7d49b80781a274ebd0b83abcff87889c9081be7a3a3e9139b2314414ab520a84`
- RAM SHA-256: `9e715fb475f286aa4a3d4a5f329f9ad310ce4abedcfb68c6a76aa60f98175cbd`
- trailer: 16바이트 모두 `00`

따라서 sector 명령은 성공했지만 DMA 목적지, 전송 크기 또는 `CdReadSync` 완료 시점 중 하나가 현재 해석과 다르다. magic 검사가 실패해 `font_ready`가 0을 유지했고 조회 훅은 BIOS fallback으로 안전하게 진행했다. 일반 BIOS 한글 표시는 아직 성공하지 않았다.

## 산출물

- [빌더](../../../tools/scripts/build_full_font_runtime.py)
- [격리 검증기](../../../tools/scripts/verify_full_font_runtime.py)
- [런타임 RAM 프로브](../../../tools/scripts/probe_full_font_runtime.py)
- [빌드 manifest](../analysis/006/build-manifest.json)
- [격리 검증 결과](../analysis/006/verification.json)
- [런타임 프로브 결과](../analysis/006/runtime-probe.json)

## 보존 상태

- 현재 실험 ROM SHA-256: `9e409a57035e693f8e8a3da0a4ee69100d5d8011aeb29c600a381cf2add3d055`
- `work/fq4/rom/`의 BIN 수: 1
- 보호된 원본과 BIOS는 수정하지 않았다.

## 다음 조사

다음 계획에서는 RAM의 실제 변경 범위와 sector별 배치를 조사하고, `CdRead` DMA 목적지 단위와 완료 조건을 런타임에서 추적한다. 원인을 고친 뒤 현재 한 개의 ROM을 다시 빌드해 RAM 해시와 일반 BIOS 화면을 검증한다.
