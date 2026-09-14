# FQ4-FINISH-014 향후 한글패치 xdelta 자동 호환

- 완료일: 2026-09-14
- 상태: **완료**
- 실행 파일: `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`

## 완료 내용

- xdelta 파일명, 날짜 및 SHA-256 고정 제한을 제거했다.
- xdelta 적용 결과 전체 SHA-256 고정 제한을 제거했다.
- ISO9660에서 `SLPS_006.04`와 `DUMMY.DUM`의 LBA와 크기를 직접 탐지한다.
- 탐지한 DUMMY.DUM LBA를 글꼴 기록 위치와 런타임 CD 읽기 코드 양쪽에 반영한다.
- PS-X EXE load address와 크기를 검증한다.
- pool 초기화 호출과 BIOS 글리프 조회 wrapper를 유일한 byte signature로 찾는다.
- 일반 BIOS용 loader 코드 영역이 비어 있는지 확인한다.
- Shift-JIS 위치 기반 문자 domain의 존재를 검사한다.
- sync, MSF header 및 XA subheader 오류가 있으면 변환 전에 거부한다.
- EDC/ECC 교정 범위를 고정 구간에서 전체 43,002 sector로 확장했다.
- 최종 sync/header/subheader/EDC/P/Q 오류가 모두 0일 때만 출력한다.
- GUI에서 `250826 한글패치` 표기를 `한글패치 xdelta`로 바꿨다.
- GUI 로그에 프로필, xdelta SHA-256, EXE/DUMMY LBA와 발견한 훅 주소를 표시한다.
- 완료 화면에 구조 프로필, 교정 sector 수 및 결과 SHA-256을 표시한다.

## 호환성 결과

- `241112`: `fq4-korean-sjis-v1` 호환, 최종 SHA-256 `ffac52e3564b302fce2c999f2a713162338e6a2bce8e1d052c559e4271b07b42`
- `250826`: `fq4-korean-sjis-v1` 호환, 기존 최종 SHA-256 `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d` 재현
- `250826` + 종족 제한 확장: 기존 SHA-256 `684d47b644f961b6552c311dffe577418f0b74ba109da7c6c25d57838beeba31` 재현
- 두 버전 모두 최종 전체 sector 오류 0
- signature 누락 및 중복 fixture 안전 거부 확인
- 배포 EXE 숨김 엔진에서 250826 전체 변환과 UTF-8 JSON protocol 확인
- GUI EXE 정상 기동 확인

## 원본 보존 및 용량

`original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않았다. 분석과 변환은 `work/fq4/rom/current.bin` 한 파일을 번갈아 재사용했고 결과 ROM을 누적하지 않았다.

## 산출물

- `tools/scripts/fq4_patch_profile.py`
- `tools/scripts/build_fq4_bios_independent.py`
- `tools/scripts/test_fq4_patch_profile.py`
- `tools/fq4_bios_independent_gui.py`
- `tools/README-fq4-gui.md`
- `docs/fq4/analysis/014/`
- `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`

최종 EXE SHA-256: `7A796EA7E8DE3D74D0629E4AE1BA3ECF678C99745055DC9DCA219F929FCBC56A`

## 적용 범위

앞으로 나오는 모든 xdelta를 무조건 허용하는 방식은 아니다. 번역 데이터가 바뀌어도 위 핵심 구조를 유지한 패치는 자동 처리하며, 실행 코드나 문자 인코딩 구조가 달라진 패치는 출력 없이 호환 불가 사유를 표시한다.
