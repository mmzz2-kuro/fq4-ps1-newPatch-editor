# FQ4-FINISH-024 세이브 에디터 대형 CLASS 이미지 추출 보정
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/024-save-editor-large-class-icon-extraction.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

CLASS 아이콘 추출기에서 대형 스프라이트 리소스를 48x48 프레임으로 처리하도록 보정했다.

기존 추출기는 모든 `Cxx.P` 파일을 16x16 타일 4개로 구성된 32x32 프레임으로 가정했다. 조사 결과 174, 183 이후 다수 리소스는 108타일이며, `12프레임 x 3x3타일` 구조로 보는 것이 맞았다. 일반 캐릭터의 앞모습 첫 프레임에 해당하는 위치는 대형 구조에서 `base_tile=36`이다.

## 구현

`tools/scripts/extract_fq4_class_icons.py`를 수정했다.

- 108타일 이상이고 9타일 프레임으로 나누어지는 리소스: `base_tile=36`, 3x3타일, 48x48 프레임
- 일반 48타일 리소스: 기존 `base_tile=16`, 2x2타일, 32x32 프레임
- 4타일 compact 리소스: `base_tile=0`, 2x2타일, 32x32 프레임
- 모든 출력 PNG는 GUI에서 흔들리지 않도록 64x64 투명 캔버스에 맞춤
- `class_catalog.json`에 `tile_layout`과 추출 방식을 기록

확인용 분석 스크립트 `tools/scripts/preview_fq4_large_class_icons.py`도 추가했다.

## 분석 산출물

- `docs/fq4/analysis/024/large-class-frame-candidates.png`
- `docs/fq4/analysis/024/large-class-fixed-preview.png`
- `docs/fq4/analysis/024/alternate-layout-candidates.png`
- `docs/fq4/analysis/024/class-174-tile-atlas.png`
- `docs/fq4/analysis/024/class-183-tile-atlas.png`
- `docs/fq4/analysis/024/class-184-tile-atlas.png`
- `docs/fq4/analysis/024/class-185-tile-atlas.png`
- `docs/fq4/analysis/024/class-186-tile-atlas.png`
- `docs/fq4/analysis/024/class-187-tile-atlas.png`
- `docs/fq4/analysis/024/class-188-tile-atlas.png`
- `docs/fq4/analysis/024/class-199-tile-atlas.png`
- `docs/fq4/analysis/024/class-200-tile-atlas.png`
- `docs/fq4/analysis/024/class-201-tile-atlas.png`
- `docs/fq4/analysis/024/class-202-tile-atlas.png`

## 검증

다음 검증을 수행했다.

- `python tools/scripts/preview_fq4_large_class_icons.py`
- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/scripts/preview_fq4_large_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 25는 기존 32x32 앞모습 규칙 유지 확인
- CLASS 174, 183, 184, 185, 186, 187, 188은 48x48 대형 앞모습 규칙 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`E5BA003D7F5FCA645531BAF4F82758FAEEE625F14EF47BDB836C978067709D4B`

## 남은 한계

CLASS 199~202의 72타일 드래곤 계열은 단순한 row-major 직사각형 프레임이 아니라, 게임 내부의 별도 타일 배치표를 사용해 조립하는 유형으로 보인다. 현재 보정은 64x64 캔버스와 3x3 프레임 규칙을 적용해 기존보다 잘림을 줄이지만, 완전한 인게임 형태 재현은 추가로 배치표 위치를 찾아야 한다.

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
