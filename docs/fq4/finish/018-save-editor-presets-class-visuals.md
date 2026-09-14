# FQ4-FINISH-018 세이브 에디터 프리셋 및 CLASS 이미지 UI

- 완료일: 2026-09-14
- 상태: **사용자 승인 이미지 조합 전체 적용 완료**
- 실행 파일: `tools/dist/FQ4-PS1-Save-Editor.exe`

## 완료 내용

- HR 1~16, HP 1~999, AT·AR·DF·DR 1~99 제한을 GUI와 저장 엔진에 적용했다.
- HR·HP·AT·AR·DF·DR 프리셋과 선택적 CLASS·LV·FT 저장을 구현했다.
- 프리셋 생성·갱신·삭제·재시작 후 복원을 구현했다.
- 캐릭터 다중 선택과 일괄 프리셋 적용을 구현했다.
- 프리셋 선택 및 관리 UI를 상단 도구 모음에서 오른쪽 `캐릭터 편집` 영역의 설명문 아래로 이동했다.
- 150개 CLASS 전용 이미지 선택 창과 ID·이름 검색을 추가했다.
- 원본 `/CHR*/Cxx.P` 파일에서 150개 실제 32×32 대표 프레임을 추출했다.
- EXE를 다시 빌드하고 실행·체크섬·변경 범위 회귀 검증을 통과했다.

CLASS 아이콘은 실제 게임 데이터의 앞모습 타일 `16=좌상`, `17=좌하`, `18=우상`, `19=우하`를 조합한다. CLASS 25 인게임 화면을 기준으로 만든 검정·은색·빨강·노랑 정규화 팔레트를 사용자가 미리보기로 승인했으며, 같은 규칙을 150개 전체에 적용했다.

## 원본 보존

`original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`는 수정하지 않았다. CLASS 그래픽은 원본 BIN을 읽기만 해서 추출했고 별도 ROM 복사본을 만들지 않았다.

## 산출물

- `tools/FQ4SaveEditor/preset_store.py`
- `tools/FQ4SaveEditor/class_catalog.json`
- `tools/FQ4SaveEditor/class_icons/`
- `tools/scripts/extract_fq4_class_icons.py`
- `tools/dist/FQ4-PS1-Save-Editor.exe`
- `docs/fq4/analysis/018/README.md`

최종 EXE SHA-256: `8CDF0B6B27976E991EA2820B8D9AAFE95EF6256C937340911AE74B6A0ADC333D`
