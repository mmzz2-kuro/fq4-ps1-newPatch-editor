# FQ4-FINISH-020 RetroArch 메모리카드 호환성 분석

- 완료일: 2026-09-14
- 상태: **호환 확인 및 에디터 지원 완료**
- 대상: `memcard/retroarch/fq4-kor-250826.srm`
- 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 분석 결론

제공된 `.srm`은 별도 RetroArch 컨테이너가 아니라 표준 131,072바이트 raw PS1 메모리카드 이미지다. 현재 에디터의 `.mcd` 처리 엔진과 내부 형식이 완전히 호환된다.

- 크기: 131,072바이트
- 선두 시그니처: `MC`
- PS1 디렉터리 체크섬: 15/15 정상
- FQ4 슬롯: 2개
- 슬롯 1: `BISLPS-00604-1`, 블록 1·2·3·4
- 슬롯 2: `BISLPS-00604-2`, 블록 5·6·7·8
- 두 슬롯 모두 FQ4 게임 내부 체크섬 정상
- 무변경 렌더링 결과가 입력과 바이트 단위로 일치

따라서 이 파일은 확장자만 `.srm`이며, 현재 `.mcd`와 동일한 방식으로 캐릭터를 편집할 수 있다.

## 에디터 변경

- 파일 열기 창에 `.mcd`와 `.srm`을 함께 표시한다.
- 형식별 `MCD 파일` 및 `RetroArch SRM 파일` 필터를 추가했다.
- `.srm`을 열면 기본 출력 이름을 `원래이름-edited.srm`으로 제안한다.
- `.mcd`를 열면 기존처럼 `원래이름-edited.mcd`를 제안한다.
- 저장 엔진과 게임 체크섬 처리 방식은 공통으로 유지한다.

## 검증 결과

- RetroArch `.srm` 파싱 및 슬롯 탐지 통과
- 무변경 바이트 왕복 통과
- 제어된 캐릭터 능력치 변경 및 재개방 확인
- 변경 후 게임 내부 체크섬 검증 통과
- `.srm` 확장자 유지 확인
- 기존 `.mcd` 전체 회귀 테스트 통과
- EXE 재빌드와 GUI 기동 확인

분석 스크립트: `tools/scripts/analyze_fq4_memory_card.py`

SRM 회귀 스크립트: `tools/scripts/test_fq4_retroarch_srm.py`

최종 EXE SHA-256: `CA1C637CB5588BFB1268745C2C15E685B6756BD2EF7088326DCE0AA9170647B7`

## 원본 보존

입력 `.srm`의 작업 전후 SHA-256은 모두 `C5A273E0FB86271285D0170DFB34BF513D9140DE4E44ADB9944467375C437B7C`로 동일하다. 원본은 수정하지 않았다. 테스트 출력은 `work/fq4/save-editor/current-retroarch-test.srm` 한 파일만 만들고 재사용하도록 구성했다.
