# PLAN-010 전체 한글 글리프 위치 교정 결과

## 원인

전체 글꼴 추출 시작점이 실제 위치보다 8바이트 앞이었다. 기존 payload는 한글 BIOS `0x69D60`에서 시작했지만, PLAN-004에서 정상 출력된 13자의 코드·BIOS offset을 역산하면 모든 글자가 `0x69D68`을 같은 시작점으로 가리킨다.

예를 들어 `간(88A1)`은 dense index 2이며 정상 BIOS offset은 `0x69DA4`다.

```text
0x69D68 + 2 * 30 = 0x69DA4
```

기존 시작점으로는 `0x69D9C`가 되어 8바이트 앞의 데이터를 반환한다. 이 때문에 각 30바이트 글리프에 앞 글리프의 행 데이터가 섞여 획이 밀린 것처럼 보였다.

## 수정

`tools/scripts/build_full_font_runtime.py`의 `FONT_BIOS_OFF`를 `0x69D60`에서 `0x69D68`로 변경했다. 글리프 stride 30바이트, 2,350자 산술 lookup, CD loader와 RAM 배치는 유지했다.

## 검증

- 정상 기준 13자의 역산 시작점: 전부 `0x69D68`
- 전체 2,350자 lookup 주소: 통과
- 디스크 payload와 BIOS 글꼴 70,500바이트: 일치
- 일반 BIOS cold boot RAM SHA-256: `44b980275ca25888762cbd595e7eb2a4b39a57e7b49187b3f486cdbd4981e539`
- `font_ready=1`, `FQ4F` trailer: 통과
- 정상 기준 13자의 실제 lookup→변환→GPU `LoadImage`: 모두 PLAN-004 해시와 일치
- Mode 2 Form 1 EDC/ECC 38개 sector와 ISO 구조: 통과

`reference-glyphs.json`에는 13자별 기존·정상 주소와 해시가 있고, `runtime-glyph-trace.json`에는 실제 GPU 업로드 검증 결과가 있다. 최종 화면 픽셀은 사용자 육안 확인 항목이다.
