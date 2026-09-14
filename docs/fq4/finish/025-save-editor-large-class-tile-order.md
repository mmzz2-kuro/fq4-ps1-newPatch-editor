# FQ4-FINISH-025 대형 CLASS 타일 순서 보정
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/025-save-editor-large-class-tile-order.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

대형 3x3 CLASS 스프라이트의 타일 순서를 사용자 확인값에 맞게 보정했다.

적용한 화면 배치는 다음과 같다.

```text
0 3 6
1 4 7
2 5 8
```

즉 파일 내 타일 순서는 `좌상, 좌중, 좌하, 중상, 중간, 중하, 우상, 우중, 우하`이며, 기존 행 우선 조합 대신 세로열 우선 조합을 사용한다.

## 구현

`tools/scripts/extract_fq4_class_icons.py`에 대형 3x3용 `column_major` 조합을 추가했다.

- 일반 2x2 리소스: 기존 행 우선 조합 유지
- 대형 3x3 리소스: 세로열 우선 조합 적용
- 출력 PNG: 기존과 동일하게 64x64 투명 캔버스에 맞춤
- `class_catalog.json`의 `tile_layout.column_major`에 적용 여부 기록

색상은 이번 작업에서 조정하지 않았다. 사용자가 해당 구간까지 게임을 진행해 인게임 색상을 확인한 뒤 별도 작업으로 반영한다.

## 확인 이미지

- `docs/fq4/analysis/025/large-3x3-column-major-preview.png`

확인 이미지에서 174, 183~198, 203~204는 세로열 우선 배치로 정상적인 형태가 확인됐다. 199~202는 형태는 잡히지만 색상과 프레임 선택이 추가 확인 대상이다.

## 검증

다음 검증을 수행했다.

- `python tools/scripts/extract_fq4_class_icons.py`
- `python -m py_compile tools/scripts/extract_fq4_class_icons.py tools/scripts/preview_fq4_large_class_icons.py tools/FQ4SaveEditor/app.py`
- `class_catalog.json` 220개 항목 확인
- CLASS 25는 기존 32x32 규칙 유지 확인
- CLASS 174, 183, 199, 203의 `tile_layout.column_major` 기록 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

최종 EXE SHA-256:

`2AE17BF868E4AB035D54B6CAD1DA97B64B7451F97BE4153D32FA6A2A1DE0280E`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.
