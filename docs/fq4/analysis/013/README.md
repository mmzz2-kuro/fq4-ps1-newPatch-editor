# PLAN-013 EDC/ECC 배드섹터 조사와 교정

## 원인

일본판 원본 43,002개 sector를 독립 검사했을 때 오류는 0개였다. 250826 xdelta 적용 직후에는 LBA 10030~22652에서 Mode 2 Form 1 sector 11,046개의 EDC, P parity와 Q parity가 모두 실패했다. 일반 BIOS 변환 전부터 존재하며 PLAN-010 결과의 실패 집합과도 정확히 같았다.

따라서 일반 BIOS 글꼴 삽입 코드가 배드섹터를 만든 것이 아니라 250826 패치가 raw sector의 payload와 일부 Form 정보를 바꾸면서 기존 280바이트 EDC/P/Q tail을 남긴 것이 원인이다. 기존 자체 검증은 우리가 직접 수정한 38개 sector만 검사해 이 넓은 구간을 놓쳤다.

## 교정

`repair_cdrom_xa_ecc.py`가 실패한 Form 1 sector마다 다음 280바이트만 다시 생성한다.

- EDC 4바이트
- P parity 172바이트
- Q parity 104바이트

sync, MSF/mode header, XA subheader와 2,048바이트 user data는 변경하지 않는다. GUI 제품 엔진은 250826 적용과 일반 BIOS 변환 후 LBA 10030~22652를 자동 교정하며 정확히 11,046개가 아니면 출력을 거부한다.

## 독립 검사

`verify_cdrom_xa_ecc.py`는 전체 raw BIN을 검사한다. 원본의 정상 Form 1 sector 40,654개를 test vector로 사용해 저장된 EDC/P/Q와 byte 단위로 모두 일치함을 확인했다. 구현 범위는 cdrkit/cdrtools libedc의 Mode 2 Form 1 구조와 대조했다.

교정 결과:

- 현재 ROM 전체 오류: 0
- Python GUI 출력 전체 오류: 0
- 단일 EXE 출력 전체 오류: 0
- 최종 ROM SHA-256: `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d`

사용자가 처음 사용한 외부 검사기의 재검사는 남아 있다.
