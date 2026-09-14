# FQ4 BIOS 독립 최소 글리프 PoC 근거

현재 판정과 지원 범위는 [FQ4-FINISH-002](../../finish/002-bios-independent-font-poc.md)를 기준으로 한다. 이 폴더의 JSON은 스크립트가 생성하는 파생 근거이며 직접 수정하지 않는다.

## 재현 명령

프로젝트 루트에서 다음을 실행한다. 빌더는 원본과 250826 xdelta를 확인하고 기존 `work/fq4/rom/current.bin` 한 파일을 초기화한 뒤 PoC를 적용한다.

```powershell
python tools/scripts/build_bios_independent_poc.py
python tools/scripts/verify_bios_independent_poc.py
python tools/scripts/compare_bios.py
```

필요한 로컬 Python 도구:

- Python 3.10.6
- Keystone Engine 0.9.2: MIPS32 little-endian 훅 어셈블
- Capstone 5.0.7: 최종 배치 명령 역어셈블
- Unicorn 2.1.4: 훅과 게임 글리프 변환 함수 격리 실행

## 파일

| 파일 | 내용 |
|---|---|
| `poc-build.json` | 입력·출력 해시, 훅과 코드, 최소 글리프 매핑, 예상 쓰기, 수정 섹터 |
| `poc-verification.json` | 세 한글 코드 반환, BIOS 폴백, 게임 변환 결과, 최종 명령열 검증 |
| `bios-comparison.json` | 사용자가 추가한 일반 BIOS와 동봉 한글 BIOS의 식별값 및 차이 범위 |
| `runtime-intervention.json` | 일반 BIOS 런타임에서 실제 게임 훅·변환·`LoadImage` 경로를 관찰한 결과 |

## PoC 배치

| 역할 | 실행 파일 오프셋 | RAM | 크기 |
|---|---:|---:|---:|
| BIOS 조회 훅 | `0x7348C` | `0x80082C8C` | 8바이트 |
| 최소 조회 코드 | `0xDD440` | `0x800ECC40` | 128바이트 |
| “교섭중” 글리프 | `0xDD500` | `0x800ECD00` | 90바이트 |

조회 코드는 `8952`, `8EB5`, `917E`만 ROM 내부 글리프로 보낸다. 나머지 코드는 원래의 `B0(51h)` 호출로 전달한다.

코드·글리프 위치는 250826 실행 파일에서 0으로 채워진 영역이다. 조사한 실행 파일의 직접 분기, 절대 포인터와 제한된 LUI/하위 주소 결합에서는 선택 구간을 가리키는 참조가 발견되지 않았다. 그러나 간접 인덱스, 범위 기반 데이터 소비와 실제 런타임 접근의 완전성은 입증하지 못했다. 이 위치는 개발 PoC 후보이며 제품 배치로 채택하지 않는다.

## 디스크 무결성 경계

- 수정 논리 파일은 `SLPS_006.04` 하나다.
- 원본 250826 이미지의 LBA 254와 466을 수정한다.
- 두 섹터는 수정 전에 Mode 2 Form 1 EDC/ECC를 다시 계산하여 저장값과 일치함을 확인했다.
- 사용자 데이터 변경 뒤 EDC와 P/Q ECC를 다시 계산했다.
- sync/header/subheader는 그대로 유지했다.
- 최종 raw 이미지에서 기준과 다른 섹터가 위 두 개뿐임을 전수 비교했다.
- ISO 파일 크기, extent와 디스크 전체 크기는 변하지 않는다.

## 일반 BIOS 비교

사용자가 `original/scph1001.bin`을 추가한 뒤 `compare_bios.py`로 별도 입력 기록을 생성했다. 최초 ROM 조사 당시의 불변 입력 목록은 역사적 기준으로 유지하고, 뒤늦게 추가된 BIOS만 `bios-comparison.json`에 보충 기록했다.

| 항목 | 일반 BIOS | 동봉 한글 BIOS |
|---|---|---|
| 크기 | 524,288바이트 | 524,288바이트 |
| SHA-256 | `71af94d1e47a68c11e8fdb9f8368040601514a42a5a399cda48c7d3bff1e99d3` | `f8658d98e32c6a8560a832c50f74f84662e1bff98c486c6480c207a2b404b88f` |
| ROM 버전 문자열 | `System ROM Version 2.2 12/04/95 A` | 동일 |

두 파일은 `0x69D68`부터 `0x7B0CB` 사이에서 67,422바이트가 다르고 이 범위 앞뒤는 완전히 같다. 기존 글리프 경로 분석과 합치므로 글리프 데이터 교체와 일관된 형태지만, 바이트 비교만으로 변경 구간의 모든 바이트 의미를 확정하지는 않는다.

## 일반 BIOS 런타임 검증

- 공식 portable DuckStation 0.1.11894를 `work/fq4/tools/duckstation/`에 준비했다.
- 실행 파일 SHA-256: `ade6b3cd7a8329a658a402f065c81136e19511962a1f5e0c1a4c30a50392cdca`.
- 출처: [공식 DuckStation 저장소](https://github.com/stenzek/duckstation), [공식 명령행 문서](https://github.com/stenzek/duckstation/wiki/Command-Line-Arguments).
- 다운로드 ZIP은 압축 해제와 해시 확인 뒤 72,669,228바이트를 삭제했다. portable 실행 파일은 후속 검증을 위해 남겼다.
- Windows Computer Use 네이티브 파이프가 없어 에뮬레이터 창 조작·캡처를 수행하지 못했다.
- 사용자가 제공한 일반 BIOS를 portable 환경의 `bios/scph1001.bin`으로 한 번 복사해 재사용했다. 원본 입력은 수정하지 않았다.
- DuckStation 로그에서 BIOS가 `SCPH-1001 ... (v2.2 12-04-95 A)`, NTSC-U로 선택되고 `current.cue`의 `SLPS-00604`가 부팅된 것을 확인했다. 일본판 디스크와 BIOS 지역 불일치 경고가 있었지만 시스템 부팅과 커널 초기화는 완료됐다.
- 정상 실행 중 실제 게임이 훅 주소 `0x80082C8C`에 일반 코드 `0x8140`을 전달한 것을 GDB로 관찰했다. 이는 일반 BIOS 폴백 경로의 런타임 도달을 입증한다.
- 화면 입력 절차가 없으므로 CPU 상태를 명시적으로 개입해 실제 렌더러 `0x800464C0`에 `8952`, `8EB5`, `917E`를 전달했다. 세 코드 모두 PoC 훅을 거쳐 실제 `LoadImage(0x800845FC)`에 도달했고, 업로드된 128바이트 해시는 동봉 한글 BIOS 기준 변환 결과와 각각 일치했다.
- 개입 전 CPU 레지스터와 임시 RAM은 복원했지만 전역·GPU 상태는 복원하지 않았으므로 증거 수집 뒤 에뮬레이터를 종료했다.

`runtime-intervention.json`은 일반 BIOS에서 실제 게임 조회·변환·GPU 업로드 호출이 연결된다는 증거다. 대표 화면의 최종 픽셀 가시성, 정상 플레이 입력만으로 해당 세 코드에 도달하는 절차, 화면 종료·재진입은 입증하지 않는다.
