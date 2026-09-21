# FQ4 FINISH-039 캐릭터 팔레트 편집 및 이미지 출력 GUI

## 완료 내용

기존 세이브 에디터의 클래스 이미지 렌더링 규칙을 독립 모듈로 복사하고, 클래스별 팔레트 인덱스의 RGB 색상을 직접 지정할 수 있는 별도 GUI 도구를 제작했다.

사용자가 입력하지 않은 클래스와 팔레트 인덱스는 기존 추출기의 색상을 사용한다. 클래스 000·010의 기존 예외 색상도 폴백에 포함된다. 팔레트 인덱스 0은 투명색으로 고정된다.

## 산출물

- 독립 렌더러: `tools/scripts/fq4_class_sprite.py`
- 검증 스크립트: `tools/scripts/verify_fq4_palette_editor.py`
- GUI: `tools/FQ4PaletteEditor/app.py`
- 사용자 팔레트 파일: `tools/FQ4PaletteEditor/class_palettes.json`
- 사용 설명: `tools/FQ4PaletteEditor/README.md`
- PyInstaller 설정: `tools/packaging/fq4_palette_editor.spec`
- 빌드 스크립트: `tools/scripts/build_fq4_palette_editor_exe.ps1`
- 실행 파일: `tools/dist/FQ4-Class-Palette-Editor.exe`
- 검증 결과: `docs/fq4/analysis/039/verification.json`

## GUI 기능

- 원본 BIN 선택과 클래스 220개 로드
- 클래스 번호·이름 목록
- 기존 타일 배치를 적용한 64×64 이미지 및 4배 확대 미리보기
- 선택 클래스가 실제로 사용하는 팔레트 인덱스 목록
- 각 인덱스의 현재 색상과 `기존/사용자/고정` 출처 표시
- HEX, R, G, B 입력 및 Windows 색상 선택기
- 인덱스별 사용자 색상 적용과 기존 색상 복원
- 클래스별 설정 JSON 불러오기와 원자적 저장
- 팔레트 인덱스를 구분하기 위한 임시 구분색 미리보기
- 선택 클래스 PNG와 전체 클래스 PNG 출력

## 배치 규칙

- 일반 클래스: 2×2, base 16
- compact 리소스: 2×2, base 0
- 대형 3×3: base 36
- class 211~216: 4×4, base 64
- class 217: 6×6, base 0
- class 218: 8×8, base 0
- 최종 출력은 모두 RGBA 64×64이며 대형 이미지는 기존 방식으로 축소·중앙 정렬한다.

## 검증 결과

- 클래스 수: 220
- 빈 사용자 팔레트와 기존 이미지의 불일치: 0개
- JSON 저장·불러오기 왕복: 통과
- class 25 인덱스 3·40 변경 시험:
  - 예상 변경 픽셀: 1,112
  - 실제 변경 픽셀: 1,112
- 전체 이미지 RGBA 64×64 검사: 통과
- class 25, 174, 211, 212, 217, 218 배치 검사: 통과
- Python 문법 검사: 통과
- PyInstaller 실행 파일 빌드: 통과
- 실행 파일 시작 검사: 통과

실행 파일 SHA-256:

`C86AF46EEC7F3509FEA9A98B3C348A9A642AAC1AFC6CD8AA27BC3D3002931C03`

## 사용 방법

1. `FQ4-Class-Palette-Editor.exe`를 실행한다.
2. 일본판 원본 BIN을 선택하고 `열기`를 누른다.
3. 클래스와 팔레트 인덱스를 선택한다.
4. HEX 또는 RGB 값을 넣고 `사용자 색상 적용`을 누른다.
5. 상단 `저장` 버튼으로 `class_palettes.json`에 저장한다.
6. 선택 클래스 또는 전체 클래스 PNG를 출력한다.

`기존 색상으로 복원`을 누르면 해당 인덱스의 사용자 값만 제거되고 기존 색상으로 돌아간다. 생성한 PNG는 별도 출력 경로에 기록되며 기존 세이브 에디터 이미지를 덮어쓰지 않는다.

## 원본 보호

- `original/`, `patched/`, `korean-patch/`, 세이브 데이터는 수정하지 않았다.
- 전체 ROM 복사본을 만들지 않았다.
- 기존 `tools/FQ4SaveEditor/class_icons/`를 수정하지 않았다.
