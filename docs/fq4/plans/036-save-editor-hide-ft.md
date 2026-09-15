# FQ4 PLAN-036: 세이브 에디터 FT 항목 GUI 숨김

작성일: 2026-09-15

## 목표

세이브 에디터의 캐릭터 편집 UI에서 `FT` 입력 항목을 숨기고, 자금 편집 영역에 게임 내 표시값 안내를 추가합니다. 세이브 구조와 내부 API에는 `ft` 값을 그대로 유지해서 기존 저장/로드와 프리셋 데이터 호환성은 깨지지 않게 합니다.

## 배경

현재 GUI는 캐릭터 레코드의 `FT`, `LV`, `HP`, `HR`, `AT`, `AR`, `DF`, `DR`을 모두 표시하고 편집합니다. 사용자 관점에서는 FT 값의 의미가 불명확하고 실수로 바꿀 필요가 적으므로, 우선 GUI에서만 보이지 않게 처리합니다.

## 작업 범위

- `tools/FQ4SaveEditor/app.py`
  - 캐릭터 편집 영역에서 `FT` Spinbox 제거
  - 캐릭터 적용 시 기존 `old.ft` 값을 그대로 사용
  - 프리셋 저장 팝업에서 `FT 포함` 체크박스 제거 또는 비표시
  - 프리셋 상세 표시에서 FT 표시는 제거
  - 기존 프리셋 파일에 `ft`가 들어 있어도 로드/적용은 기존 호환성을 위해 유지 가능
  - 자금 편집 영역에 “게임 내 표시 자금은 입력값 × 10” 안내 추가

- `tools/FQ4SaveEditor/README.md`
  - 편집 항목 설명에서 FT 제거
  - 자금 배율 안내 추가

## 원본 보존 원칙

- 원본 ROM, 패치, 메모리카드 샘플은 수정하지 않습니다.
- GUI 소스와 README만 수정합니다.
- 필요 시 EXE를 다시 빌드합니다.

## 검증

- Python 문법 검사

```powershell
python -m py_compile tools/FQ4SaveEditor/app.py tools/FQ4SaveEditor/preset_store.py tools/scripts/fq4_memcard.py
```

- 세이브 에디터 EXE 재빌드

```powershell
powershell -ExecutionPolicy Bypass -File tools\scripts\build_fq4_save_editor_exe.ps1
```

## 완료 문서

작업 완료 후 아래 문서를 작성합니다.

- `docs/fq4/finish/036-save-editor-hide-ft.md`
