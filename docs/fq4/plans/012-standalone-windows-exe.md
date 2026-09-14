# FQ4-PLAN-012 — GUI 단일 Windows EXE 패키징 계획

- 작성일: 2026-09-13
- 상태: **사용자 확인 대기**
- 선행 결과: [FQ4-FINISH-011](../finish/011-bios-independent-patch-gui.md)
- 소스 GUI: `tools/fq4_bios_independent_gui.py`
- 완료 문서 예정: `docs/fq4/finish/012-standalone-windows-exe.md`

## 1. 목적

Python이 설치되지 않은 Windows에서도 실행할 수 있도록 PLAN-011 GUI와 변환 엔진을 단일 EXE로 패키징한다.

예정 결과물:

```text
tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe
```

사용자는 EXE를 실행한 뒤 일본판 원본 BIN, 250826 한글패치, 한글 BIOS, `xdelta.exe`와 출력 경로를 선택한다. 생성 결과와 검증 기준은 PLAN-011 Python GUI와 동일하게 유지한다.

## 2. 선행 구조 수정

현재 GUI는 별도 Python 프로세스로 `tools/scripts/build_fq4_bios_independent.py`를 실행한다. 단일 frozen EXE에서는 이 스크립트와 Python 실행 파일 경로가 존재하지 않을 수 있으므로 다음과 같이 정리한다.

- 제품용 엔진의 `build()` 함수를 GUI process 내부 worker thread에서 직접 호출한다.
- 진행 상태는 stdout JSON 대신 callback으로 GUI에 전달한다.
- 취소 상태는 thread-safe event로 전달한다.
- xdelta 작업은 별도 process로 유지하되 취소 시 해당 process만 종료하고 임시 BIN을 제거한다.
- 명령행 엔진은 기존 사용자를 위해 같은 `build()` 함수를 호출하는 wrapper로 유지한다.
- 개발용 고정 workspace 경로와 frozen resource 경로를 분리한다.

## 3. 패키징 방식

- PyInstaller의 `--onefile --windowed` 구성을 사용한다.
- tkinter, 해시·파일 처리 코드와 필요한 MIPS 조립/디스크 수정 모듈을 포함한다.
- 콘솔 창은 표시하지 않는다.
- `xdelta.exe`, 원본 ROM, 한글패치와 BIOS는 EXE에 포함하지 않고 사용자가 선택한다.
- 실행 중 PyInstaller 임시 압축 해제 폴더에는 프로그램 코드만 존재하며 전체 ROM은 출력 폴더의 임시 BIN 한 개만 사용한다.
- spec 파일을 `tools/packaging/`에 두어 같은 EXE를 재현할 수 있게 한다.

## 4. 의존성 처리

- 현재 프로젝트의 capstone, keystone 및 디스크 EDC/ECC 코드를 frozen 환경에서 import할 수 있는지 확인한다.
- 실제 제품 빌드에 사용되지 않는 Unicorn·GDB·DuckStation 분석 모듈은 포함하지 않는다.
- PyInstaller hidden import와 binary dependency는 실제 import 분석 결과에 따라 최소화한다.
- PyInstaller 버전을 고정해 `tools/packaging/requirements.txt`에 기록한다.
- 빌드 스크립트는 `tools/scripts/build_fq4_gui_exe.ps1`에 작성한다.

PyInstaller가 현재 환경에 없으면 고정 버전을 설치해야 한다. 설치가 필요한 시점에는 sandbox 승인 절차를 사용한다.

## 5. 원본 보존과 용량 규칙

- `original/`, `patched/`, `korean-patch/`와 BIOS는 수정하지 않는다.
- 패키징 과정은 ROM을 포함하거나 복사하지 않는다.
- GUI 기능 시험에는 기존 `work/fq4/rom/current.bin`과 출력 임시 BIN 한 개만 사용한다.
- 시험용 전체 ROM은 해시 비교 직후 제거한다.
- PyInstaller의 `build/` 중간 산출물은 검증 완료 후 제거하고 최종 EXE와 spec·로그만 유지한다.
- 기존 결과 EXE가 있으면 같은 파일을 원자적으로 교체하며 날짜별 EXE 복사본을 누적하지 않는다.

## 6. EXE 동작 검증

### 정적 검증

- EXE가 PE32+ Windows GUI 실행 파일인지 확인한다.
- SHA-256, 파일 크기와 PyInstaller 버전을 기록한다.
- 원본 ROM, xdelta, BIOS 또는 전체 한글 글꼴 payload가 별도 파일 형태로 동봉되지 않았는지 검사한다.
- spec에서 분석용 불필요 모듈이 제외됐는지 확인한다.

### GUI 검증

- Python 환경변수와 프로젝트 현재 경로에 의존하지 않고 EXE가 실행되는지 확인한다.
- 다른 작업 폴더에서 실행해 파일 선택 창과 기본 상태가 정상인지 확인한다.
- 한글·공백 경로와 긴 경로에서 입력 및 출력 경로가 유지되는지 확인한다.
- 지원하지 않는 241112 패치와 잘못된 BIOS가 출력 전에 차단되는지 확인한다.
- 처리 중 중복 실행 방지, 취소, 창 닫기와 임시 파일 정리를 확인한다.

### 결과 ROM 검증

- EXE로 생성한 BIN SHA-256이 PLAN-010/011 결과인 `95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e`와 정확히 일치하는지 확인한다.
- CUE의 파일명, `MODE2/2352`와 UTF-8 처리를 검사한다.
- 생성 BIN을 기존 검증기로 검사한다.
- 시험용 출력 BIN/CUE를 삭제하고 전체 작업 ROM 한 개 조건을 다시 확인한다.

## 7. 배포 구성

최종적으로 다음 파일만 사용자용 산출물로 유지한다.

- `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- `tools/README-fq4-gui.md`
- `tools/packaging/fq4_gui.spec`
- `tools/packaging/requirements.txt`
- `tools/scripts/build_fq4_gui_exe.ps1`

EXE에는 저작권이 있는 원본 ROM, 한글패치 xdelta, BIOS와 `xdelta.exe`를 포함하지 않는다.

## 8. 통과 기준

- Python이 없는 실행 조건을 모사한 환경에서 EXE가 독립 실행된다.
- EXE의 GUI와 오류 처리가 PLAN-011과 동일하게 작동한다.
- 검증된 입력으로 생성한 BIN/CUE가 PLAN-011 결과와 byte 단위로 일치한다.
- 실패·취소 시 불완전한 출력과 임시 전체 ROM이 남지 않는다.
- 원본 입력은 수정되지 않고 최종 EXE 한 개만 유지된다.
- 빌드가 spec과 PowerShell 스크립트로 재현된다.

## 9. 산출 문서

- `docs/fq4/analysis/012/exe-build.json`: 도구 버전, EXE 크기와 해시
- `docs/fq4/analysis/012/exe-runtime-verification.json`: 독립 실행과 GUI 검사
- `docs/fq4/analysis/012/rom-reproducibility.json`: EXE 결과 ROM 비교
- `docs/fq4/analysis/012/README.md`: 빌드·실행·한계
- `docs/fq4/finish/012-standalone-windows-exe.md`: 완료 문서

## 10. 사용자 확인

- 승인 상태: **확인 대기**
- 승인 시 실행 범위: frozen 호환 구조 수정, PyInstaller 고정 버전 설치·spec 작성, 단일 EXE 빌드, EXE와 결과 ROM 검증
- 외부 설치 가능성: PyInstaller가 없을 경우 패키지 설치 승인이 별도로 표시될 수 있음
