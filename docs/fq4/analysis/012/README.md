# PLAN-012 단일 Windows EXE 결과

PyInstaller 6.11.0의 onefile/windowed 방식으로 Python이 필요 없는 64비트 Windows GUI를 생성했다.

```text
tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe
```

GUI와 변환 worker는 같은 EXE에 들어 있다. GUI가 변환을 시작하면 EXE가 `--engine-json` 내부 모드로 자기 자신을 실행하므로 외부 Python이나 프로젝트의 `.py` 파일을 사용하지 않는다. `xdelta.exe`, 원본 ROM, 250826 패치와 한글 BIOS는 사용자가 선택한다.

frozen 환경에서 누락됐던 Keystone 동적 라이브러리를 spec에 명시적으로 포함했다. 최종 EXE는 콘솔 창을 표시하지 않으며 시스템 임시 폴더를 작업 디렉터리로 한 독립 실행 시험을 통과했다.

EXE 내장 worker로 한글·공백 경로에 생성한 ROM은 PLAN-010/011 결과와 byte 단위로 일치했다. 시험 BIN/CUE와 PyInstaller 중간 빌드 디렉터리는 검증 후 제거했다.

빌드 재현:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/scripts/build_fq4_gui_exe.ps1
```

고정 의존성은 `tools/packaging/requirements.txt`, PyInstaller 구성은 `tools/packaging/fq4_gui.spec`에 기록돼 있다.
