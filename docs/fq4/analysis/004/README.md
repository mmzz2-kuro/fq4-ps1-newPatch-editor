# FQ4 PLAN-004 지도 메뉴 글리프 PoC 근거

## 재현 명령

```powershell
python tools/scripts/analyze_menu_strings.py
python tools/scripts/build_menu_glyph_poc.py
python tools/scripts/verify_menu_glyph_poc.py
```

일반 BIOS로 DuckStation의 GDB 서버를 연 뒤 `python tools/scripts/runtime_menu_probe.py`를 실행한다. 이 검사는 CPU 상태를 개입해 실제 게임 렌더러에 코드를 전달하므로 정상 플레이 입력이나 최종 화면 캡처를 대신하지 않는다.

## 문자열 코드열

| 문자열 | 게임 코드열 | `SLPS_006.04` 위치 |
|---|---|---:|
| `시간경과` | `8F62 88A1 88E4 88F8` | `0x12D0` |
| `부대이동` | `8DCC 8AE9 90CA 8B5E` | `0x12DE` |
| `탐색` | `935C 8E96` | `0x12EC`, `0xD5D1B` |

앞의 세 위치는 같은 지도 메뉴 문자열 블록에 연속으로 있다. `탐색`은 다른 문맥에도 한 번 더 사용된다. 인코딩은 KS X 1001의 행·열을 같은 JIS 위치로 옮겨 Shift-JIS 바이트로 저장한 형태다. 선행 표본 `교→8952`, `섭→8EB5`, `중→917E`와 일치하며 이번 코드열도 실행 파일에서 확인됐다.

## 글리프와 PoC 배치

메뉴의 중복 제거 글리프는 `시`, `간`, `경`, `과`, `부`, `대`, `이`, `동`, `탐`, `색` 10개다. 기존 `교`, `섭`, `중`을 유지해 총 13개를 넣었다.

| 역할 | RAM | 크기 |
|---|---:|---:|
| 테이블 조회 코드 | `0x800ECC40` | 116바이트 |
| 코드→글리프 인덱스 테이블 | `0x800ECCC0` | 52바이트, 13개 항목 |
| 글리프 데이터 | `0x800ECD00` | 390바이트 |

250826 실행 파일의 `0x800ECC40..0x800ED630`은 2,544바이트 0 영역이다. 이번 배치는 582바이트 범위 안에 들어간다. 정적 직접 참조 조사에는 충돌이 없지만 간접·범위 소비의 완전성은 입증되지 않았으므로 제품용 안전 공간으로 승인하지 않는다.

## 런타임에서 발견한 결함

첫 테이블 구현은 `lhu` 직후 로드된 값을 사용했다. Unicorn 격리 실행은 통과했지만 실제 R3000A 런타임에서는 로드 지연 때문에 잘못된 글리프가 업로드됐다. 두 `lhu` 뒤에 `nop`을 추가했고 검증기에 load-delay 감사를 넣었다.

수정 후 일반 BIOS DuckStation 런타임에서 13개 코드 모두 실제 게임 렌더러 `0x800464C0`, 조회 훅 `0x80082C8C`, 기존 변환 함수와 `LoadImage 0x800845FC`를 통과했다. 업로드 버퍼의 SHA-256은 각각 격리 변환 기준과 일치했다.

## 디스크 변경과 제한

- 출력 ROM SHA-256: `1911cfe9d9ca963a2761414c5df0881115759628ffdea637c97f8dbf62da3b86`
- 크기: 101,140,704바이트
- 수정 논리 파일: `SLPS_006.04`
- 기준과 다른 raw 섹터: LBA 254, 466
- Mode 2 Form 1 EDC 및 P/Q ECC 재계산 완료
- 작업용 전체 ROM: `work/fq4/rom/current.bin` 한 벌

현재 결과는 코드열, 글리프 매핑, ROM 조회, 변환과 GPU 업로드 호출을 입증한다. 일반 BIOS 지도 메뉴의 최종 픽셀은 새 캡처가 필요하다.

## 근거 파일

- `menu-strings.json`: 문자열 코드열과 디스크 위치
- `menu-glyphs.json`: 10개 메뉴 글리프의 BIOS 위치와 해시
- `poc-build.json`: 13개 글리프 PoC 배치와 변경 감사
- `poc-verification.json`: 정적·격리 실행 결과
- `runtime-intervention.json`: 일반 BIOS의 실제 게임 업로드 호출 결과
