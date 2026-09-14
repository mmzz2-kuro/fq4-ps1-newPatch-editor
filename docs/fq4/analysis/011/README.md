# PLAN-011 일반 BIOS용 한글 ROM 생성 GUI

## 구현

`tools/fq4_bios_independent_gui.py`는 Python 표준 tkinter 기반 Windows GUI다. 원본 BIN, 250826 xdelta, 한글 BIOS, xdelta 실행 파일과 출력 BIN을 선택할 수 있다. 작업은 별도 thread와 subprocess에서 실행되며 단계별 상태와 오류를 창에 표시한다.

`tools/scripts/build_fq4_bios_independent.py`는 GUI와 분리된 제품용 엔진이다. 입력을 SHA-256으로 판정하고 250826 한글패치를 임시 BIN 한 개에 적용한 뒤 PLAN-010의 일반 BIOS용 loader와 2,350자 글꼴을 삽입한다. 완성 결과가 검증된 SHA-256과 다르면 출력으로 확정하지 않는다.

## 재현 결과

GUI 엔진 결과는 PLAN-010 `current.bin`과 byte 단위로 일치했다.

```text
95bb338e4f836f37323b9011491f0fd7e376b31b4fc5514bccd6bf613f0df83e
```

한글과 공백이 포함된 경로에서 BIN과 UTF-8 BOM CUE 생성을 확인했다. 241112 패치, 기존 출력, 잘못된 입력은 변환 전에 차단된다. 실패 시험 후 임시 BIN이 남지 않았고 전체 시험 ROM도 삭제했다.

## 사용

```text
python tools/fq4_bios_independent_gui.py
```

자세한 사용 방법은 `tools/README-fq4-gui.md`에 있다. 현재 결과는 Python GUI이며 단일 EXE 패키징은 포함하지 않는다.
