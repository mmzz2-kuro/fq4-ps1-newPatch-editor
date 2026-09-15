# FQ4 PLAN-033 완료: 세이브 에디터 자금 및 보유 아이템 편집

작성일: 2026-09-15

## 완료 내용

세이브 에디터에 자금과 보유 아이템 편집 기능을 추가했습니다.

- `tools/scripts/fq4_memcard.py`
  - 자금 읽기/쓰기 API 추가: payload `0x0692`, little-endian `uint16`, 범위 `0..65535`
  - 보유 아이템 API 추가: payload `0x0492..0x051F`, 2바이트 반복 `item_id u8 / quantity u8`
  - 아이템 수량 제한: `0..99`
  - 기존 아이템 수량 갱신, 없는 아이템 첫 빈 칸 추가, 선택 칸 삭제 지원
  - 모든 변경 후 FQ4 내부 체크섬 8개 재계산

- `tools/FQ4SaveEditor/app.py`
  - 우측 패널에 `자금 / 보유 아이템` 영역 추가
  - 자금 적용 버튼 추가
  - 아이템 목록 표시 추가
  - 아이템 ID/수량 입력 후 `추가/수정` 지원
  - 선택 아이템 삭제 지원
  - GUI 문구를 한글로 재정리

- `tools/FQ4SaveEditor/README.md`
  - 자금/아이템 편집 사용법과 빌드 명령 갱신

## 검증

원본 메모리카드는 수정하지 않고 `work/fq4/033/` 아래 작업 복사본으로 검증했습니다.

- 첫 번째 샘플 슬롯에서 자금 `12356 -> 12357` 변경 확인
- 기존 아이템 수량 증가 확인
- 없는 아이템을 첫 빈 칸에 추가 확인
- 저장 후 `MemoryCard.open()`으로 재오픈 확인
- 렌더 크기 `131072` bytes 확인
- `.mcd`와 RetroArch `.srm` 샘플에서 자금/아이템 목록 읽기 확인
- FQ4 슬롯이 없는 `.srm`은 `no BISLPS-00604-* saves found`로 정상 제외
- Python 문법 검사 통과

```powershell
python -m py_compile tools/scripts/fq4_memcard.py tools/FQ4SaveEditor/app.py tools/FQ4SaveEditor/preset_store.py
```

세이브 에디터 EXE도 다시 빌드했습니다.

```powershell
powershell -ExecutionPolicy Bypass -File tools\scriptsuild_fq4_save_editor_exe.ps1
```

빌드 산출물:

- `tools/dist/FQ4-PS1-Save-Editor.exe`
- SHA-256: `AB1940994E9D5E4273D819F96B9CF5DF9F19CCC50D14DEDE1F6E949F74C86F74`

## 남은 주의점

아이템 ID와 실제 아이템명 매핑은 아직 확정하지 않았습니다. 현재 GUI는 ID를 기준으로 표시합니다. 이후 게임 화면이나 ROM 내 아이템명 테이블이 확인되면 아이템명 표시를 추가할 수 있습니다.
