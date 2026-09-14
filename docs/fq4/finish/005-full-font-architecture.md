# FQ4-FINISH-005 전체 글꼴 구조 설계

- 완료일: 2026-09-13
- 결과: **부분 통과 — 구조 확정, 구현 단계 실행 검증 필요**
- 계획: [005-full-font-architecture.md](../plans/005-full-font-architecture.md)

## 결론

2,350자 전체 글꼴은 70,500바이트라 실행 파일 뒤에 붙이면 참조 중인 RAM 영역과 충돌한다. 글꼴을 디스크의 기존 더미 extent에 저장하고, 시작 시 게임 메모리 풀 상단에 읽은 뒤 기존 글리프 훅에서 주소를 계산하는 구조로 진행한다.

## 확정 구조

1. 한글 BIOS의 JIS 행 `0x30..0x48`에서 2,350개 글리프를 30바이트 단위로 추출한다.
2. `/DUMMY.DUM;1`의 LBA와 크기를 유지하고 선두 35개 Form 1 payload 섹터에 헤더와 글꼴을 기록한다.
3. 게임 주 메모리 풀 상단 70,656바이트를 예약한다.
4. CD 초기화 뒤 35개 섹터를 읽고 완료 후 `font_ready`를 설정한다.
5. 조회 훅은 Shift-JIS를 JIS 행·셀로 바꾸고 `index=(row-0x30)*94+(cell-0x21)`, `address=font_base+index*30`을 계산한다.
6. 준비 전이나 범위 밖 코드는 기존 BIOS `B0(51h)`로 전달한다.

## 검증 수치

- 전체 글꼴: 2,350자, 70,500바이트
- 저장: 35섹터, payload 71,680바이트, 여유 1,180바이트
- 정적 확인: 730자, 7,946회
- 고립 후보 포함: 867자
- BIOS heap: 483,208바이트
- 예약 후 게임 풀 추정: 412,552바이트
- 조회식: 유효 코드 2,350개와 무효 경계값 전부 통과

## 산출물

- [분석 스크립트](../../../tools/scripts/analyze_full_font_architecture.py)
- [조회 검증 스크립트](../../../tools/scripts/verify_full_font_lookup_design.py)
- [분석 재현 문서](../analysis/005/README.md)
- [전체 인코딩 맵](../analysis/005/encoding-map.json)
- [사용 글리프 조사](../analysis/005/used-glyphs.json)
- [저장 구조](../analysis/005/storage-options.json)
- [RAM 구조](../analysis/005/ram-loader-options.json)
- [조회 검증](../analysis/005/lookup-verification.json)

## 보존 확인

- `current.bin` SHA-256: `1911cfe9d9ca963a2761414c5df0881115759628ffdea637c97f8dbf62da3b86`
- `work/fq4/rom/`의 BIN 수: 1
- ROM을 쓰거나 새 전체 ROM 복사본을 만들지 않았다.

## 다음 단계

PLAN-006에서는 `DUMMY.DUM` 런타임 미사용 여부와 CD 읽기 함수를 먼저 확인한 후, 글꼴 35섹터 갱신과 EDC/ECC 재계산, RAM 예약·로더·조회 훅을 `current.bin` 한 개에 구현한다. 일반 BIOS에서 전투, 부대 이동, 맵 전환, 세이브·로드와 장시간 진행을 검사한다.
