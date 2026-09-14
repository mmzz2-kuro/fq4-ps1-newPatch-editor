# FQ4-FINISH-023 세이브 에디터 한글패치 이름표 반영
- 완료일: 2026-09-14
- 계획 문서: `docs/fq4/plans/023-save-editor-korean-patched-names.md`
- 대상 도구: `tools/FQ4SaveEditor/`
- 최종 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 결과

세이브 에디터의 캐릭터 이름 목록을 한글패치 ROM 기준으로 다시 생성했다. 한글패치 ROM의 PS-X EXE 이름 테이블은 원본의 CP932 이름표와 다르게, 패치 영문 이름과 커스텀 단일 바이트 한글 글리프가 섞여 있었다.

`tools/scripts/generate_fq4_editor_names.py`를 재작성해 다음 흐름으로 재생성하게 했다.

- `patched/First Queen IV - Varcia Senki (kor).bin`의 캐릭터 이름 테이블을 1차 입력으로 사용한다.
- ASCII 항목은 패치 ROM의 영문 이름을 그대로 사용한다.
- 커스텀 한글 글리프 바이트는 명시적 byte-to-Hangul 매핑으로 해독한다.
- 빈 항목은 원본 이름표 기반 fallback을 유지한다.
- 클래스 이름은 이번 작업 대상이 아니므로 기존 `class_names.json`을 덮어쓰지 않는다.

## 생성 현황

- 캐릭터 이름 항목: 640개
- 클래스 이름 항목: 220개 유지
- 패치 영문 이름: 530개
- 커스텀 한글 글리프 해독 이름: 101개
- 빈 항목 fallback: 9개
- 미해독 커스텀 바이트: 0개

사용자가 지적한 `트리스렌`은 name_id 265에서 한글로 표시된다.

## 검증

다음 검증을 수행했다.

- `python tools/scripts/generate_fq4_editor_names.py`
- `python -m py_compile tools/scripts/generate_fq4_editor_names.py tools/FQ4SaveEditor/app.py tools/scripts/fq4_memcard.py`
- `character_names.json` 640개, `class_names.json` 220개 확인
- MCD와 RetroArch SRM에서 name_id 265가 `트리스렌`으로 표시되는지 확인
- `powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_save_editor_exe.ps1`

확인된 `트리스렌` 위치:

- `memcard/First Queen IV - Varcia Senki (Japan)_1.mcd`: slot 1, 2, 3
- `memcard/First Queen IV - Varcia Senki (Japan)_1-edited.mcd`: slot 1, 2, 3
- `memcard/retroarch/fq4-kor-250826.srm`: slot 1, 2

최종 EXE SHA-256:

`131A6208BB541C59FBF592FB874B16FA03A5AD6A73E07FDB2BF9447D16FBA5E0`

## 산출물

- 수정: `tools/scripts/generate_fq4_editor_names.py`
- 갱신: `tools/FQ4SaveEditor/character_names.json`
- 분석 기록: `docs/fq4/analysis/023/korean-name-extraction.json`
- 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 읽기만 했고 수정하지 않았다. ROM 전체 복사본은 추가로 만들지 않았다.

## 남은 주의점

커스텀 한글 바이트는 패치 ROM의 실제 폰트 글리프를 사람이 읽은 매핑에 기반한다. 현재 미해독 바이트는 없지만, 게임 화면에서 특정 이름의 표기가 다르게 보이면 해당 바이트 매핑 하나를 고치면 같은 바이트를 쓰는 이름들이 함께 정리된다.
