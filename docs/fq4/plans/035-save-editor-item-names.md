# FQ4 PLAN-035: 세이브 에디터 아이템명 추출 및 표시

작성일: 2026-09-15

## 목표

세이브 에디터의 보유 아이템 목록이 현재 `아이템 ID`만 표시하므로, 한글패치된 ROM 또는 관련 패치 자료에서 아이템 이름 테이블을 찾아 GUI에 반영합니다. 최종적으로 자금/아이템 편집 영역에서 ID와 함께 실제 아이템명을 표시하고, 아이템 추가/수정 입력도 이름을 보고 선택할 수 있게 개선합니다.

## 배경

PLAN-033에서 보유 아이템 구조는 payload `0x0492..0x051F`의 2바이트 반복 구조로 구현했습니다.

- `item_id u8`
- `quantity u8`
- GUI 수량 제한: `0..99`
- 없는 아이템은 첫 빈 칸에 추가

현재 남은 문제는 `item_id`가 실제 게임 내 어떤 아이템인지 알기 어렵다는 점입니다. 아이템 편집은 ID만으로도 가능하지만, 사용자용 GUI로 쓰려면 이름 표시가 필요합니다.

## 원본 보존 원칙

- `original/`, `patched/`, `korean-patch/`, `memcard/`, `savestates/`, `dos-save/`의 원본 파일은 수정하지 않습니다.
- 분석 결과와 임시 파일은 `work/fq4/035/` 아래에 둡니다.
- 분석 스크립트는 `tools/scripts/`에 작성합니다.
- GUI 자료 파일은 `tools/FQ4SaveEditor/`에 추가합니다.
- 최종 GUI 실행 파일은 기존처럼 `tools/dist/FQ4-PS1-Save-Editor.exe`를 갱신합니다.

## 조사 대상

1. `patched/`의 한글패치 적용 ROM
   - 한글패치 기준 아이템명을 우선합니다.
   - 세이브 에디터 사용자는 한글패치 환경을 기준으로 볼 가능성이 높습니다.

2. `korean-patch/` 자료
   - xdelta만 있으면 직접 테이블 확인은 어려울 수 있습니다.
   - 텍스트/스크립트/도구 자료가 있으면 아이템명 후보 추출에 사용합니다.

3. `original/`의 원본 ROM
   - 한글 테이블 추출이 어려운 경우 일본어 원문 아이템명을 대조합니다.
   - 한글명과 일본어명을 함께 보관할 수 있는 구조를 고려합니다.

## 작업 계획

1. 아이템 ID 사용 범위 정리
   - 기존 메모리카드 샘플에서 등장한 `item_id` 목록을 다시 수집합니다.
   - GUI에 필요한 최소 매핑 범위와 전체 후보 범위를 분리합니다.

2. ROM/패치 자료에서 아이템명 후보 검색
   - 현재 프로젝트의 텍스트 인코딩 자료와 추출 스크립트를 확인합니다.
   - 한글패치 ROM 안에서 아이템명으로 보이는 짧은 문자열 목록을 찾습니다.
   - 일본어 원본 ROM과 차이를 비교해 같은 테이블인지 확인합니다.

3. ID와 이름 매핑 검증
   - 세이브 아이템 ID 목록과 ROM 내 이름 배열 순서를 대조합니다.
   - 가능하면 DOS 에디터 자료의 아이템명 목록도 보조 근거로 비교합니다.
   - 확실한 항목과 추정 항목을 구분해 문서화합니다.

4. 세이브 에디터 자료 파일 추가
   - `tools/FQ4SaveEditor/item_names.json` 생성
   - 형식 후보:

```json
[
  {"id": 1, "name": "...", "source": "patched-rom", "confidence": "confirmed"}
]
```

5. GUI 반영
   - 아이템 목록에 `아이템명` 컬럼 추가
   - 아이템 추가/수정 입력에 이름 선택 콤보박스 추가
   - 선택 시 ID가 자동 입력되도록 처리
   - 이름이 없는 ID는 기존처럼 `Item 0xNN` fallback 유지

6. 검증
   - `.mcd`, `.srm` 샘플 로드 확인
   - 기존 아이템 목록에 이름 표시 확인
   - 이름 선택 후 아이템 추가/수정 확인
   - 저장 후 재오픈/checksum 검증 확인
   - `python -m py_compile` 실행
   - EXE 재빌드

7. 완료 문서 작성
   - `docs/fq4/finish/035-save-editor-item-names.md`
   - 추출 경로, 매핑 신뢰도, GUI 변경점, 검증 결과 기록

## 예상 산출물

- `tools/scripts/analyze_fq4_item_names.py` 또는 동등한 분석 스크립트
- `docs/fq4/analysis/035/` 분석 결과
- `tools/FQ4SaveEditor/item_names.json`
- `tools/FQ4SaveEditor/app.py` 갱신
- `tools/FQ4SaveEditor/README.md` 갱신
- `tools/dist/FQ4-PS1-Save-Editor.exe` 재빌드
- `docs/fq4/finish/035-save-editor-item-names.md`

## 리스크와 확인 포인트

- 아이템 ID가 ROM 테이블 순서와 1:1로 맞지 않을 수 있습니다.
- 한글패치 ROM의 아이템명이 압축되어 있거나 공용 문자열 테이블에 섞여 있을 수 있습니다.
- 일부 아이템은 게임 내 미사용/이벤트 전용일 수 있으므로 이름 매핑 신뢰도를 구분해야 합니다.
- 매핑이 불확실한 항목은 GUI에 추정 표시를 남기거나 ID fallback을 유지합니다.
