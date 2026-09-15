# FQ4-FINISH-034 엔딩 후 결산 화면 수정 옵션

작성일: 2026-09-15

## 결과

엔딩 동영상 이후 검은 화면과 캐릭터 결산 화면 라벨 깨짐을 GUI 빌드 옵션으로 반영했다.

새 GUI 옵션:

- `엔딩 후 결산 화면 수정 적용 (권장)`
- 기본값: 켜짐
- 엔진 인자: `--fix-ending-result`

적용 내용:

- `/MOV/MOV04.STR;1` raw sector LBA `18430..22652`를 원본 ROM의 MOV04로 대체한다.
- `/SLPS_006.04;1` 논리 오프셋 `0xE0400`의 결산 화면 템플릿을 원본 구조 기준으로 복구한다.
- 라벨만 내장 한글 폰트 로더가 사용하는 game_code 바이트로 치환한다.

치환 라벨:

| 원본 | 적용 |
|---|---|
| `名前` | `이름` |
| `クラス` | `직업` |
| `パワー` | `파워` |
| `討数` | `격추` |
| `戦場より生還！` | `전장에서생환!` |
| `にて死亡` | `에서사망` |

## 변경 파일

- `tools/scripts/build_fq4_bios_independent.py`
- `tools/fq4_bios_independent_gui.py`
- `tools/README-fq4-gui.md`
- `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`

## 검증

엔진 검증 빌드:

```text
python tools/scripts/build_fq4_bios_independent.py --original original/...Japan.bin --patch korean-patch/퍼스트퀸4 한글패치(241112).xdelta --bios korean-patch/SCPH1001.BIN --xdelta-exe korean-patch/xdelta.exe --output work/fq4/034/gui-ending-option-verify.bin --overwrite --fix-ending-result
```

결과:

- 출력 BIN: `work/fq4/034/gui-ending-option-verify.bin`
- SHA-256: `8ebb90d9a4fd382d44af13c71b9bbd52f70fb3bb98b0415bad1344ab8e0e8aad`
- sync/header/subheader/EDC/P/Q 오류: 0
- MOV04 대체 LBA: `18430..22652`
- 결산 템플릿 변경 LBA: `472`

GUI EXE 빌드:

```text
powershell -ExecutionPolicy Bypass -File tools/scripts/build_fq4_gui_exe.ps1
```

결과:

- EXE: `tools/dist/FQ4-Standard-BIOS-Korean-Tool.exe`
- SHA-256: `82FC1A06451F1D67D522E673BB5E45DC59C3CE3DFED44A7B713B5A7BDA06A5F3`

## 남은 확인

사용자 런타임 확인 기준:

1. 일반 BIOS에서 한글 메뉴가 정상 표시된다.
2. 최종 보스 이후 엔딩 동영상이 재생된다.
3. 동영상 후 캐릭터 결산 화면으로 진입한다.
4. 살아있는 캐릭터는 `전장에서생환!` 문구가 표시된다.
5. 사망 캐릭터는 장소명 뒤 `에서사망` 문구가 표시된다.
6. 결산 후 타이틀로 복귀한다.

원본 ROM, 기존 패치본, xdelta 파일은 수정하지 않았다.
