# FQ4 PLAN-036 완료: 세이브 에디터 FT 숨김 및 자금 안내 추가

작성일: 2026-09-15

## 완료 내용

세이브 에디터 GUI에서 `FT` 편집 항목을 숨겼습니다. 세이브 구조와 내부 캐릭터 레코드에는 `ft` 값을 그대로 유지하므로, 파일 로드/저장과 기존 데이터 호환성은 유지됩니다.

추가로 자금 편집 영역에 아래 안내 문구를 넣었습니다.

```text
게임 내 표시 자금은 입력값 × 10으로 반영됩니다.
```

## 변경 파일

- `tools/FQ4SaveEditor/app.py`
  - 캐릭터 편집 Spinbox 목록에서 `FT` 제거
  - 캐릭터 적용 시 `old.ft`를 그대로 사용하도록 변경
  - 프리셋 저장 팝업에서 `FT 포함` 체크박스 제거
  - 프리셋 상세 표시에서 FT 항목 제거
  - 자금 편집 영역에 게임 내 표시 배율 안내 추가

- `tools/FQ4SaveEditor/README.md`
  - 편집 항목 설명에서 FT 제거
  - 자금 입력값과 게임 내 표시값의 `×10` 관계 설명 추가

- `docs/fq4/plans/036-save-editor-hide-ft.md`
  - 자금 안내 추가 범위 반영

## 검증

Python 문법 검사를 통과했습니다.

```powershell
python -m py_compile tools/FQ4SaveEditor/app.py tools/FQ4SaveEditor/preset_store.py tools/scripts/fq4_memcard.py
```

세이브 에디터 EXE를 다시 빌드했습니다.

```powershell
powershell -ExecutionPolicy Bypass -File tools\scripts\build_fq4_save_editor_exe.ps1
```

빌드 산출물:

- `tools/dist/FQ4-PS1-Save-Editor.exe`
- SHA-256: `AB1940994E9D5E4273D819F96B9CF5DF9F19CCC50D14DEDE1F6E949F74C86F74`

## 비고

기존 프리셋 파일에 `ft` 값이 들어 있는 경우에도 내부 프리셋 검증과 적용 로직은 호환을 유지합니다. 다만 새 GUI에서는 FT 값을 새 프리셋에 포함하도록 선택하는 UI를 제공하지 않습니다.
