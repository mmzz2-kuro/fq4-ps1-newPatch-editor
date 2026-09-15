# FQ4 PLAN-035 완료: 세이브 에디터 아이템명 추출 및 표시

작성일: 2026-09-15

## 완료 내용

세이브 에디터의 보유 아이템 편집 영역에 한글 아이템명을 반영했습니다.

- 한글패치 실행 파일에서 아이템명 테이블 72개를 추출했습니다.
- 테이블 시작 오프셋은 `0xE67D5`, 항목 폭은 17 bytes입니다.
- 세이브 아이템 ID는 1-based로 매핑했습니다.
- `tools/FQ4SaveEditor/item_names.json`을 생성했습니다.
- GUI 보유 아이템 목록에 `아이템명` 컬럼을 추가했습니다.
- 아이템 이름 선택 콤보박스를 추가했습니다.
- 이름을 선택하면 ID가 자동 입력되도록 했습니다.
- 매핑되지 않은 ID가 있을 때는 `Item 0xNN` fallback을 유지합니다.

## 변경 파일

- `tools/scripts/analyze_fq4_item_names.py`
- `docs/fq4/analysis/035/README.md`
- `docs/fq4/analysis/035/item-name-table.json`
- `docs/fq4/analysis/035/item-term-search.json`
- `tools/FQ4SaveEditor/item_names.json`
- `tools/FQ4SaveEditor/app.py`
- `tools/FQ4SaveEditor/README.md`
- `tools/packaging/fq4_save_editor.spec`

## 검증

- 아이템명 72개 생성 확인
- `memcard/` 샘플에서 확인된 고유 아이템 ID 47개가 모두 1..72 범위 안에 있음을 확인
- Python 문법 검사 통과

```powershell
python -m py_compile tools/scripts/analyze_fq4_item_names.py tools/FQ4SaveEditor/app.py tools/FQ4SaveEditor/preset_store.py tools/scripts/fq4_memcard.py
```

- 세이브 에디터 EXE 재빌드 완료

```powershell
powershell -ExecutionPolicy Bypass -File tools\scripts\build_fq4_save_editor_exe.ps1
```

빌드 산출물:

- `tools/dist/FQ4-PS1-Save-Editor.exe`
- SHA-256: `AB1940994E9D5E4273D819F96B9CF5DF9F19CCC50D14DEDE1F6E949F74C86F74`

## 남은 확인점

아이템명 테이블과 세이브 ID는 현재 샘플 기준으로 모두 일치합니다. 후반 세이브에서 73 이상의 아이템 ID가 발견되면 테이블 범위를 다시 조사해야 합니다.
