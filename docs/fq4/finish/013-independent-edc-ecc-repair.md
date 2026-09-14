# FQ4-FINISH-013 독립 EDC/ECC 검사 및 배드섹터 교정

- 완료일: 2026-09-13
- 결과: **기술 검증 통과, 사용자 외부 검사 재확인 대기**
- 계획: [PLAN-013](../plans/013-independent-edc-ecc-repair.md)
- 분석: [analysis/013](../analysis/013/README.md)

## 원인

250826 xdelta 적용 직후부터 LBA 10030~22652의 Mode 2 Form 1 sector 11,046개가 잘못된 EDC/P/Q를 가지고 있었다. 원본 ROM은 전체 오류 0개이며 일반 BIOS 변환이 추가한 오류도 없었다. 기존 검증기는 일반 BIOS 작업에서 직접 수정한 38개 sector만 검사했기 때문에 이 문제를 놓쳤다.

## 수정

- 11,046개 sector의 EDC 4바이트, P 172바이트, Q 104바이트를 재계산했다.
- 현재 `current.bin`을 교정했다.
- Python GUI 엔진에 자동 교정 단계를 추가했다.
- 단일 Windows EXE를 같은 경로에 재빌드했다.
- 전체 43,002개 sector 검사기를 추가했다.

## 최종 검증

- sync 오류: 0
- header 오류: 0
- XA subheader 오류: 0
- EDC 오류: 0
- P parity 오류: 0
- Q parity 오류: 0
- 일반 BIOS `font_ready=1`: 통과
- 전체 한글 글꼴 해시: 유지
- Python GUI와 EXE 결과 SHA-256: 일치

## 갱신된 파일

- 작업 ROM SHA-256: `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d`
- EXE SHA-256: `11a39d203ef2a53f1ab875a41a2b10b3cbd569325839137eb6086c10ce34eb63`
- EXE: `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`

시험용 전체 ROM과 PyInstaller 중간 파일은 삭제했으며 `work/fq4/rom/current.bin` 한 벌만 유지했다. `original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않았다.

사용자가 처음 배드섹터를 확인한 외부 검사기로 새 GUI/EXE 출력 BIN을 다시 검사하는 확인만 남아 있다.
