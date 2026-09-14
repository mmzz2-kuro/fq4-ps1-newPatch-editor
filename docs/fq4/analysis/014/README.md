# PLAN-014 향후 xdelta 구조 호환성 분석

## 결론

`241112`와 `250826`은 전체 ROM 및 실행 파일 SHA-256은 서로 다르지만 일반 BIOS용 글꼴 로더에 필요한 핵심 구조가 같다. 두 패치 모두 `fq4-korean-sjis-v1` 프로필로 자동 판정되며 변환과 전체 EDC/ECC 검증을 통과했다.

## 공통 구조

- raw 이미지: 101,140,704바이트, 43,002 sector
- `SLPS_006.04`: LBA 24, 1,075,200바이트
- PS-X EXE load address: `0x80010000`
- `DUMMY.DUM`: LBA 24,184, 38,230,976바이트
- pool 초기화 호출: `0x80013A38`
- BIOS 글리프 조회 훅: `0x80082C8C`
- loader 영역: `0x800ECC40..0x800ECF50`
- 훅 signature는 각각 실행 파일에서 유일하며 loader 영역은 비어 있다.
- Shift-JIS 위치 기반 lookup domain은 241112에서 15,217쌍/1,389개 고유 코드, 250826에서 15,240쌍/1,401개 고유 코드가 확인됐다.

## 버전별 결과

| 버전 | xdelta 적용 결과 SHA-256 | 일반 BIOS용 최종 SHA-256 |
|---|---|---|
| 241112 | `56efd993ffae15709bf3230c27e5fab35d3461616a31a95fbc56263ca65586b3` | `ffac52e3564b302fce2c999f2a713162338e6a2bce8e1d052c559e4271b07b42` |
| 250826 | `9363cdfa247d38f5f819f5e79a25ff25ada3b2394f887726f29231da6ccbffb5` | `616ae2e0e44949b9217b94de336fc2e279e621e8753039d0a77818829f59c45d` |

250826에 부대 종족 제한 확장을 함께 적용한 결과도 기존 SHA-256 `684d47b644f961b6552c311dffe577418f0b74ba109da7c6c25d57838beeba31`와 일치했다.

## EDC/ECC

두 xdelta 결과 모두 구조 오류는 없었고 Mode 2 Form 1의 EDC/P/Q가 각각 11,046 sector에서 갱신이 필요했다. 빌더는 더 이상 고정 LBA 범위를 사용하지 않고 43,002개 전체를 검사한다. 최종 결과는 sync, header, XA subheader, EDC, P, Q 오류가 모두 0일 때만 확정된다.

## 미래 패치 판정

xdelta 파일명, 날짜, SHA-256과 적용 결과 전체 SHA-256은 허용 조건으로 사용하지 않는다. 일본판 원본과 한글 BIOS identity는 계속 고정 검증한다. 새 xdelta는 ISO 파일, EXE header/load address, 유일한 두 훅 signature, 빈 loader 영역, 문자 domain 및 raw sector 구조를 모두 통과해야 한다. signature가 없거나 중복되거나 코드 영역이 사용 중이면 출력 없이 구체적인 이유로 중단한다.

## 산출물

- `profile-241112.json`
- `profile-250826.json`
- `compatibility-tests.json`
- `ecc-tests.json`
- `tools/scripts/fq4_patch_profile.py`
- `tools/scripts/test_fq4_patch_profile.py`
