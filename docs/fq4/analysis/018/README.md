# PLAN-018 프리셋 및 CLASS 이미지 분석

## 수치 제한

저장 엔진과 GUI에서 HR 1~16, HP 1~999, AT·AR·DF·DR 1~99를 강제한다. LV는 0~255, FT는 0~65535의 기존 저장 형식을 유지한다. 프리셋 검증도 같은 범위를 사용한다.

## 프리셋

프리셋은 HR·HP·AT·AR·DF·DR을 기본 필드로 저장하고 CLASS·LV·FT는 선택적으로 포함한다. 사용자 설정은 `%APPDATA%\FQ4SaveEditor\presets.json`에 원자적으로 저장된다. 손상된 JSON은 `.invalid.json`으로 분리한 뒤 빈 목록으로 복구한다. 목록에서 여러 캐릭터를 선택해 한 번에 적용할 수 있다.

## CLASS 그래픽

ISO9660 파일표에서 CLASS ID와 `/CHR*/Cxx.P`가 직접 대응함을 확인했다. ID 0은 `/CHR0/C00.P`, ID 149는 `/CHR9/C95.P`이다. 사용자 확인으로 앞모습은 16×16 타일 `16=좌상`, `17=좌하`, `18=우상`, `19=우하`임을 확정했으며, 150개 모두 32×32 이미지로 재구성했다.

`class_catalog.json`에는 CLASS ID, 이름, 원본 파일 경로, LBA, 타일 위치와 프레임 SHA-256을 기록했다. 연속 BGR555 팔레트로 추정했던 `GRBUF1.COM + 0xCC`는 실제 화면과 일치하지 않아 폐기했다. 색상은 CLASS 25 인게임 화면의 검정 윤곽·은색 갑옷·빨간 천·노란 장식과 픽셀 인덱스 영역을 대조해 만든 사용자 승인 정규화 팔레트다. 상태는 `user_approved_front_frame_normalized_palette`로 기록한다.

## 검증

- 150개 CLASS entry와 150개 PNG 존재
- 모든 entry에 원본 경로·LBA·프레임 SHA-256 기록
- 프리셋 저장·재로드 및 여섯 수치의 경계 밖 입력 거부
- PLAN-017의 무변경 왕복, 제한된 변경, 손상 체크섬 거부와 2번 슬롯 화면 대조 통과
- 단일 EXE가 Windows에서 응답 가능한 GUI 창으로 실행됨
