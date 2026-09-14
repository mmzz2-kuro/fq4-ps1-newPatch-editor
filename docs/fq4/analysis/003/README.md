# FQ4 PLAN-003 일반 BIOS 시각 런타임 검증 근거

## 판정

자동화 실행 당시에는 **미해결**이었으나, 이후 사용자가 같은 지도 메뉴를 일반 BIOS와 동봉 한글 BIOS로 각각 캡처하여 화면 비교가 가능해졌다. 현재 PoC는 선택한 메뉴 문자열에 필요한 글리프를 포함하지 않으므로 일반 BIOS 화면에서 메뉴 문자가 한자·기호 형태로 잘못 표시된다. 동봉 한글 BIOS 화면에서는 `시간경과`, `부대이동`, `탐색`이 정상 표시된다.

## 재현 명령

검증 종료 뒤 프로젝트 루트에서 다음 명령으로 입력 해시, 부팅 로그와 단일 작업 ROM 상태를 다시 기록한다.

```powershell
python tools/scripts/finalize_visual_runtime.py
```

생성 파일:

- `runtime-visual-verification.json`: 입력 식별값, 부팅 표식, 자동화 실패와 미확인 항목
- `screenshot-comparison.json`: 사용자 캡처의 해시·크기와 화면 판정
- `work/fq4/003/duckstation.log`: 이번 새 부팅의 DuckStation 로그
- `work/fq4/003/normal-bios-menu.png`: 일반 BIOS 지도 메뉴
- `work/fq4/003/korean-bios-menu.png`: 동봉 한글 BIOS 지도 메뉴

## 확인된 내용

- DuckStation은 `original/scph1001.bin`과 해시가 같은 로컬 BIOS 복사본을 선택했다.
- BIOS는 v2.2 NTSC-U, 디스크는 NTSC-J로 기록됐다.
- 게임 ID `SLPS-00604`, 시스템 부팅과 커널 초기화가 로그에 남았다.
- 작업 ROM은 `work/fq4/rom/current.bin` 한 벌뿐이다.
- 두 캡처는 1200×914로 같은 크기이며 같은 지도 메뉴 장면이다.
- 일반 BIOS에서는 메뉴 글리프가 잘못 선택되고, 동봉 한글 BIOS에서는 한글 메뉴가 정상 표시된다.

## 미확인 내용

- `시간경과`, `부대이동`, `탐색`에 사용된 패치 코드와 전체 글리프 목록
- 이 글리프를 ROM에 넣은 다음 일반 BIOS에서의 최종 픽셀
- 화면 종료·재진입과 VRAM 상태 수명

Computer Use는 최초 초기화에서 `Trusted RPC service is not configured`가 발생했다. 대체 API 호출도 지원되지 않았고, 세션 초기화 뒤 재시도에서는 Windows 샌드박스의 deny-read ACL 적용 실패로 커널이 종료됐다. 화면이나 입력 상태를 확인할 수 없는 상태에서 좌표나 키 입력을 추정하지 않았다.

사용자 제공 캡처는 자동화 실패와 별개의 시각 근거다. 현재 비교가 입증하는 것은 이 메뉴가 여전히 한글 BIOS 글리프에 의존한다는 사실이다. 선택 문자열의 ROM 내장 글리프 구현 성공을 입증하지는 않는다.
