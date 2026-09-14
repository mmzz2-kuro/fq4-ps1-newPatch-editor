# FQ4-FINISH-029 CLASS 213~218 4x4 아이콘 반영
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/029-save-editor-4x4-class-icons-213-218.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

CLASS 213~218도 사용자 지시에 따라 4x4 `base_tile=64` 규칙으로 반영했다. 이에 따라 211~218 전체가 같은 4x4 대형 리소스 계열로 처리된다.

적용 규칙:

```text
class_id = 211..218
base_tile = 64
width_tiles = 4
height_tiles = 4
column_major = true
```

색상은 이번 작업에서 조정하지 않았다.

## 확인

확인용 이미지:

- `docs/fq4/analysis/029/class-211-218-4x4-check.png`

이미지 확인 결과 211~216은 4x4 base 64로 온전한 형태가 나온다. 217~218은 같은 규칙을 적용했지만 여전히 조각처럼 보여, 별도 프레임 선택 또는 특수 배치가 필요할 가능성이 있다.

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 211~218: 4x4 base 64 column-major 기록 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`6EE72C6E54636A496936B3A1E2780D9E7BF2509F94A89BDAC2F905C29959A6CC`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
