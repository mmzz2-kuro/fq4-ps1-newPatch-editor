# PLAN-009 분석 결과

낮은 staging buffer가 필요하다는 가설을 교차 시험했으나, 높은 주소도 정상적으로 CD DMA를 받았다. 실패 원인은 `GAME_CD_READ`의 sector 인자에서 150을 미리 뺀 것이었다.

`0x8008F600`은 sector 값을 `0x8008C708`에 넘기고 그 함수가 CD lead-in 150 frame을 자체적으로 더해 MSF로 변환한다. 정상 PVD 호출 `(1, 16, 0x801179BC)`가 BIN sector 16의 PVD를 반환한 것이 직접 증거다. 따라서 DUMMY.DUM의 BIN sector 24184는 `24034`가 아니라 `24184`로 호출해야 한다.

수정 빌드는 sector `24184..24218`을 높은 상주 영역에 직접 읽는다. 일반 BIOS cold boot에서 `font_ready=1`, 글꼴 SHA-256과 trailer가 일치했다. staging buffer와 CPU 복사 루프는 불필요하므로 추가하지 않았다.

재현 명령:

```text
python tools/scripts/build_menu_glyph_poc.py
python tools/scripts/build_full_font_runtime.py
python tools/scripts/verify_full_font_runtime.py
```

런타임 검증은 DuckStation GDB server에서 `0x800ECD18`에 중단점을 놓고 `tools/scripts/probe_font_at_breakpoint.py`로 수행했다.
