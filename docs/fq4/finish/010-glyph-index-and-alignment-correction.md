# FQ4-FINISH-010 전체 한글 글리프 위치 교정

- 완료일: 2026-09-13
- 결과: **기술 검증 통과, 사용자 화면 확인 대기**
- 계획: [PLAN-010](../plans/010-glyph-index-and-alignment-correction.md)
- 분석: [analysis/010](../analysis/010/README.md)

## 완료 내용

한글 글리프가 밀려 보인 원인은 문자 코드 변환식이나 RAM 정렬이 아니라 한글 BIOS 글꼴 추출 시작점의 8바이트 오차였다.

- 수정 전: `0x69D60`
- 수정 후: `0x69D68`
- 글리프 크기: 30바이트 유지
- 전체 글리프: 2,350자 유지

PLAN-004에서 정상 표시된 13자의 BIOS offset을 dense index로 역산했으며 모두 `0x69D68`에 일치했다. 수정 후 13자 전부 실제 게임의 조회 훅, 변환 함수와 GPU `LoadImage`를 통과했고 정상 PoC의 변환 데이터 해시와 일치했다.

## 검증 결과

- 13자 정상 기준 byte 대조: 통과
- 2,350개 코드 주소 전수 검사: 통과
- 일반 BIOS runtime 적재: 통과
- runtime 글꼴 주소: `0x801E6528`
- `font_ready`: `1`
- 수정 글꼴 SHA-256: `44b980275ca25888762cbd595e7eb2a4b39a57e7b49187b3f486cdbd4981e539`
- `FQ4F` trailer: 통과
- 13자 실제 GPU 업로드 해시: 전부 통과
- ISO 파일 398개와 DUMMY.DUM extent: 유지
- EDC/ECC 검사 sector: 38개 통과

최종 메뉴 화면의 픽셀 상태는 사용자가 일반 BIOS로 확인해야 한다.

## 현재 작업 ROM

- 파일: `work/fq4/rom/current.bin`
- SHA-256: `95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e`
- 크기: 101,140,704바이트
- 전체 BIN 개수: 1개

`original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않았다.
