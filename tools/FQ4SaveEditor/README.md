# 퍼스트퀸4 PS1 세이브 에디터

`FQ4-PS1-Save-Editor.exe`는 First Queen IV PS1 raw 메모리카드 파일(`.mcd`, `.srm`)을 열어 FQ4 세이브 슬롯을 편집합니다. DuckStation과 RetroArch의 128KiB raw 메모리카드 형식을 처리합니다.

## 주요 기능

- 캐릭터 CLASS, LV, HP, HR, AT, AR, DF, DR 편집
- 한글패치 ROM에서 추출한 캐릭터 이름 표시
- CLASS 이미지 목록과 선택 캐릭터의 CLASS 이미지 미리보기
- 능력치 프리셋 저장/적용
- 현재 파일 저장과 다른 이름으로 저장
- 자금 편집
- 보유 아이템 목록 표시, 한글 아이템명 표시, 기존 아이템 수량 수정, 없는 아이템 추가, 선택 아이템 삭제

## 자금/아이템 편집

자금은 세이브 payload `0x0692`의 little-endian `uint16` 후보를 사용합니다. GUI 입력 범위는 `0..65535`입니다. 게임 내 표시 자금은 입력한 값의 10배로 반영됩니다.

아이템은 payload `0x0492`부터 `0x0520` 직전까지 2바이트 반복 구조로 처리합니다. 각 항목은 `item_id u8`, `quantity u8`입니다. GUI에서는 한글 아이템명을 표시하며, 이름 선택 콤보박스를 고르면 ID가 자동 입력됩니다. 아이템 ID를 10진수 또는 `0x2A` 같은 16진수로 직접 입력할 수도 있고, 수량은 `0..99`로 제한합니다. 수량 0은 기존 아이템 삭제로 처리합니다.

## 저장 방식

편집 내용은 메모리에 먼저 적용됩니다. `현재 파일 저장` 또는 `다른 이름으로 저장`을 눌러야 파일에 기록됩니다. 저장 시 FQ4 내부 체크섬 8개를 다시 계산하고, 저장된 파일을 재오픈해 검증합니다.

`현재 파일 저장`은 덮어쓰기 확인 메시지를 표시합니다.

## 빌드

```powershell
powershell -ExecutionPolicy Bypass -File tools\scriptsuild_fq4_save_editor_exe.ps1
```

빌드 결과는 `tools/dist/FQ4-PS1-Save-Editor.exe`입니다.
