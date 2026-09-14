# FQ4-FINISH-012 GUI 단일 Windows EXE

- 완료일: 2026-09-13
- 결과: **완료**
- 계획: [PLAN-012](../plans/012-standalone-windows-exe.md)
- 분석: [analysis/012](../analysis/012/README.md)

## 최종 결과물

- EXE: `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- 크기: 14,992,062바이트
- SHA-256: `58ade5d840f2bf4cc2768755319fab1c0fce2ba2b978fa836cf8c886b8421292`
- 형식: PE32+ x86-64 Windows GUI
- 패키징: PyInstaller 6.11.0, onefile, windowed

Python이 설치되지 않은 환경을 모사해 프로젝트 밖의 시스템 임시 폴더에서 EXE를 실행했다. GUI process가 정상 유지됐고 콘솔 창은 생성되지 않았다.

## 변환 검증

EXE 내부 worker로 한글과 공백이 포함된 경로에 BIN/CUE를 생성했다.

- worker 종료 코드: 0
- 결과 BIN 크기: 101,140,704바이트
- 결과 SHA-256: `95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e`
- PLAN-010/011 결과와 byte 단위 일치
- UTF-8 BOM CUE 및 `MODE2/2352`: 통과

## 보존 및 정리

- EXE에 원본 ROM, 한글패치, BIOS와 `xdelta.exe`를 포함하지 않았다.
- 검증용 전체 ROM과 CUE를 삭제했다.
- PyInstaller 중간 빌드 디렉터리를 삭제했다.
- 최종 EXE는 한 개만 유지했다.
- 전체 작업 ROM은 기존 `work/fq4/rom/current.bin` 한 벌만 유지했다.
- `original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않았다.

빌드 spec, 고정 의존성과 재현 스크립트는 각각 `tools/packaging/fq4_gui.spec`, `tools/packaging/requirements.txt`, `tools/scripts/build_fq4_gui_exe.ps1`에 있다.
