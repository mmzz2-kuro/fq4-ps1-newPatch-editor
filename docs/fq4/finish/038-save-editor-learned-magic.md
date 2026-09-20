# FQ4 PLAN-038 완료: 배운 마법 편집

완료일: 2026-09-20

## 결과

세이브 에디터 상단에 `배운 마법 편집` 버튼을 추가했다. 캐릭터를 선택한 뒤 열면 현재 클래스의 마법을 최대 5개까지 선택할 수 있다. 클래스에 마법 목록이 없으면 편집을 거부한다. 게임 세이브는 마법을 CLASS ID별로 저장하므로 같은 클래스의 캐릭터 모두에게 적용된다는 안내를 창에 표시한다. 적용 후에는 기존 `현재 파일 저장` 또는 `다른 이름으로 저장`을 사용한다.

한글패치 ROM의 마법 이름 1..42를 표시한다. 이름이 확인되지 않은 ID 43..53은 숫자와 `미확인 마법`으로 보여 기존 값을 잃지 않게 했다.

## 변경 파일

- `tools/scripts/fq4_memcard.py`: 클래스별 마법 목록 읽기·쓰기, 최대 5개·중복·범위·저장 공간 검사, 체크섬 갱신
- `tools/FQ4SaveEditor/app.py`: 선택 캐릭터의 목록 표시와 마법 편집 창
- `tools/FQ4SaveEditor/spell_names.json`: 한글패치 ROM의 마법명
- `tools/packaging/fq4_save_editor.spec`: 마법명 자료 포함
- `tools/scripts/analyze_fq4_magic.py`, `generate_fq4_spell_names.py`, `test_fq4_magic.py`: 분석·재생성·검증
- `docs/fq4/analysis/038/`: 구조와 샘플 대조 근거

## 검증

- 메모리카드 11개 슬롯의 클래스별 목록을 읽었다.
- 자동 검증에서 8개 슬롯 파싱, 한 클래스 편집 후 재읽기, 다른 영역 보존, 체크섬, 중복·비마법 클래스 거부, 원래 값 복원 시 바이트 단위 일치를 확인했다.
- GUI 생성과 아레스(220) 편집 창의 5개 선택 칸 생성을 확인했다.
- `py_compile`과 PyInstaller 빌드가 통과했다.
- 기존 `test_fq4_memcard.py`의 스크린샷 수치 대조 부분은 현재 사용자 메모리카드의 수치와 달라 실패한다. 이번 변경의 마법 테스트는 통과했다.

기존 `tools/dist/FQ4-PS1-Save-Editor.exe`가 실행 중이라 Windows가 덮어쓰기를 거부했다. 새 실행 파일은 `tools/dist/FQ4-PS1-Save-Editor-Magic.exe`로 별도 제공한다. SHA-256: `3EE6BAEED2DFE8059CB2710609D78397AB6EAFFE350FF1401E57EC3BDBD54402`.

## 남은 확인

변경된 세이브를 게임에서 불러와 마법 메뉴 표시와 실제 시전을 확인해야 한다. ID 43..53의 이름과 클래스별 시전 제한도 게임 또는 추가 ROM 분석으로 확인할 수 있다.
