# FQ4 전체 한글 글리프 구조 분석

PLAN-005는 ROM을 변경하지 않고 문자 사용량, 한글 BIOS 글리프 영역, 디스크 저장 후보, RAM 적재 구조와 조회식을 조사했다.

## 재현

```powershell
python tools/scripts/analyze_full_font_architecture.py
python tools/scripts/verify_full_font_lookup_design.py
```

두 스크립트는 보호된 입력을 읽기만 한다.

## 결과

- KS X 1001 완성형 한글은 JIS 행 `0x30..0x48`, 셀 `0x21..0x7E`에 대응하는 2,350자이다.
- 한글 BIOS의 연속 글리프 영역은 `0x69D60..0x7B0CB`, 글리프당 30바이트, 총 70,500바이트이다.
- 실행 파일 변경 구간에서 연속 문자열 기준 730자를 확인했고 고립 후보를 합치면 867자이다.
- 정적 추출의 누락 가능성 때문에 전체 2,350자를 쓰는 구성이 안전하다.
- 전체 글꼴은 2,048바이트 payload 35개 섹터에 들어간다.
- `/DUMMY.DUM;1`은 LBA 24184, 38,230,976바이트이며 실행 파일에 파일명 참조가 없다. 기존 extent의 선두 35개 섹터가 저장 후보이다.
- BIOS heap은 `0x80182068..0x801F7FF0`이다. 주 메모리 풀 상단 70,656바이트를 예약하면 추정 412,552바이트가 남는다.
- 조회식 `(row-0x30)*94+(cell-0x21)`은 유효 코드 2,350개와 범위 밖 경계 검사를 모두 통과했다.

## 산출물

`encoding-map.json`, `text-candidates.json`, `used-glyphs.json`, `storage-options.json`, `ram-loader-options.json`, `lookup-design.json`, `lookup-verification.json`에 세부 근거가 있다.

## 구현 전 확인

`DUMMY.DUM`이 게임 진행이나 seek timing에 사용되지 않는다는 실행 증명과, 메모리 풀을 70,656바이트 줄인 상태의 장시간 회귀 검사가 필요하다. 정확한 CD 읽기 함수와 완료 동기화 지점은 PLAN-006에서 추적한다.
