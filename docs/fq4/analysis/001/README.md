# FQ4 초기 분석 근거

현재 결론과 미해결 위험의 기준 문서는 [작업 완료 기록](../../finish/001-rom-analysis.md)이다. 이 폴더의 JSON·CSV는 아래 스크립트가 생성하는 측정 근거이며, 직접 수정하지 않는다.

## 재현 환경과 명령

- Python 3.10.6, Capstone 5.0.7, Unicorn 2.1.4, Pillow.
- Capstone은 MIPS32 little-endian 해석기로 제한된 명령열을 조사했다. PS1 전체 ISA·제어 흐름 완전성이나 신규 코드 생성 검증을 주장하지 않는다.
- 동봉 xdelta 3.0u의 파일 해시는 `inputs.json`에 고정했다. 배포 출처·번들 권한은 이번 분석에서 확정하지 않았으며 도구를 재배포하지 않는다.
- 패키지는 `work/fq4/python-deps/`에만 설치했다. 시스템 Python 패키지 구성은 변경하지 않았다.

프로젝트 루트에서:

```powershell
python -m pip install --target work/fq4/python-deps capstone==5.0.7 unicorn==2.1.4
python tools/scripts/survey_rom.py
# current.bin이 필요할 때만 실행. 기존 작업용 경로를 재사용한다.
korean-patch/xdelta.exe -d -f -s "original/First Queen IV - Varcia Senki (Japan).bin" "korean-patch/퍼스트퀸4 한글패치(250826).xdelta" work/fq4/rom/current.bin
python tools/scripts/inspect_bios_path.py
python tools/scripts/probe_glyphs.py
python tools/scripts/finalize_survey.py
```

`probe_glyphs.py` 실행에는 `work/fq4/001/reproduced/SLPS_006.04`가 필요하다. `inspect_bios_path.py`가 작업용 이미지에서 이 실행 파일만 추출한다. 전체 ROM 복사본은 추가하지 않는다. Pillow는 설치된 환경의 버전을 `tool-environment.json`에 기록한다.

선택 영역 역어셈블:

```powershell
python tools/scripts/trace_executable.py 0x800464c0 --kind reproduced --size 0x308
python tools/scripts/trace_executable.py 0x800464c0 --refs
python tools/scripts/trace_executable.py 0xbfc160e0 --bios --size 0x90
```

BIOS 파일에 저장된 코드는 RAM으로 옮겨 실행되는 부분이 있다. `--bios`는 저장 위치 기준 출력이므로 표시된 JAL 목적지를 그대로 BIOS 내부 런타임 주소로 해석하면 안 된다. 격리 실험의 명시적 재배치 가정은 `glyph-probe.json`에 기록되어 있다.

## 근거 목록

| 파일 | 의미 |
|---|---|
| `inputs.json`, `input-preservation.json` | 입력 식별과 종료 시 보존 검증 |
| `survey.json`, `original-files.json`, `patched-files.json` | 디스크 구조와 398개 파일 목록 |
| `diff-ranges.csv`, `changed-sectors.json`, `file-differences.json` | 원본과 제공된 241112 패치본의 차이 |
| `patch-lineage.json` | 두 xdelta의 스트리밍 출력 해시 재현 |
| `reproduction.json` | 250826 재현본과 제공된 241112 패치본의 차이 |
| `bios-identity.json`, `bios-candidates.json` | 동봉 BIOS 식별 및 참조 후보 |
| `bios-candidate-disassembly.txt`, `renderer-disassembly.txt`, `renderer-direct-references.txt` | 제한된 실행 코드 조사 |
| `bios-function-disassembly.txt`, `glyph-probe.json` | BIOS 함수·게임 글리프 변환 함수 격리 관찰 |
| `text-map.json` | 대표 텍스트 표본, 가역 토큰, 조사 범위와 표시 경로 |
| `final-checks.json` | 변경 섹터 귀속, 입력 보존, 작업용 ROM 수 |

## 분석 한계

- Form 2를 포함하는 XA 파일의 해시는 논리 바이트가 아닌 ISO extent에 대응하는 전체 raw 섹터 기준이다. `hash_basis`로 구별한다.
- 최초 파서는 Form 2 파일을 Form 1로 읽는 것을 오류로 거부했다. XA를 별도 raw 해시 기준으로 처리한 뒤 재실행했다. 이를 임의의 2048-byte 데이터로 정규화하지 않았다.
- 디스크 쓰기·재빌드·EDC/ECC 전체 유효성 검사·실제 GPU 소비·정상 게임 플레이·실기 실행은 수행하지 않았다.
- 스크립트의 후보 탐색은 전체 문자열·참조를 검증하는 제품 빌드 도구가 아니다. 표본 토큰 왕복과 격리 함수 실행도 게임 전체 호환성의 증거가 아니다.
