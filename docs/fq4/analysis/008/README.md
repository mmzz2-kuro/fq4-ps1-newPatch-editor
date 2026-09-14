# PLAN-008 분석 결과

정상 게임의 `0x8008F600` 호출을 추적해 실제 ABI를 `(sector count, ISO logical LBA, destination)`으로 수정했다. raw LBA 24184의 logical LBA는 24034이다.

글꼴 요청을 정상 게임과 같은 1-sector 단위 35회로 바꾼 결과 모든 Setloc과 DataSector가 오류 없이 끝났다. 따라서 interrupt 비활성 문맥이라는 PLAN-008 가설은 기각됐다.

정상 PVD 호출 `(1, 16, 0x801179BC)`은 목적지에 `01 CD001 01 PLAYSTATION` 데이터를 남긴다. 글꼴 호출 `(1, 24034..24068, 0x801E6528부터)`은 SDK 진입 인자와 CD sector 완료가 정확하지만 목적지 데이터가 변하지 않았다. 다음 조사는 낮은 주소의 검증된 staging buffer를 사용한 읽기와 high-memory 복사를 비교해야 한다.
