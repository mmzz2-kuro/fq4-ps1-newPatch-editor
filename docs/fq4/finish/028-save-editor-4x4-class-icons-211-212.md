# FQ4-FINISH-028 CLASS 211~212 4x4 아이콘 반영
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/028-save-editor-4x4-class-icons-211-212.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

CLASS 211, 212를 사용자 확인값에 따라 4x4 `base_tile=64` 프레임으로 반영했다.

두 리소스는 192타일이며, 기존 2x2/3x3 규칙으로는 일부만 보였다. 확인용 후보 이미지에서 `4x4 base 64`가 올바른 정면 프레임으로 확인됐다.

## 구현

`tools/scripts/extract_fq4_class_icons.py`의 `layout()`에 CLASS 211, 212 특별 처리를 추가했다.

```text
class_id 211, 212
base_tile = 64
width_tiles = 4
height_tiles = 4
column_major = true
```

기존 2x2 규칙과 3x3 대형 규칙은 유지했다. 색상은 이번 작업에서 조정하지 않았다.

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 25: 기존 2x2 column-major 유지 확인
- CLASS 174/183: 기존 3x3 column-major 유지 확인
- CLASS 211/212: 4x4 base 64 column-major 확인
- `docs/fq4/analysis/028/class-211-212-4x4-check.png` 생성 및 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`C73BA3AAEB9849BCBF53AFCA9078F09D1CEF7D9EA34948914982F20D57C38E6E`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
