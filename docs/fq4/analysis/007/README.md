# PLAN-007 분석 결과

전체 RAM fingerprint 검색 결과 35개 글꼴 sector의 데이터는 PS1 RAM 어디에도 기록되지 않았다. 이후 덮어쓰기가 아니라 DMA interrupt가 전달되지 않은 상태였다.

정상 게임 호출부 `0x8008F600`은 `(destination, ISO logical LBA, sector count)`를 받고 내부에서 150 sector를 더해 MSF로 변환한다. 따라서 raw LBA 24184의 입력은 24034이다. 수정 뒤 `Setloc 05:22:34`와 raw LBA 24184 접근은 맞았지만 DuckStation은 각 sector에 `Data interrupt was not delivered`를 기록했다.

현재 malloc 직후 주입 지점에서는 CD interrupt 처리가 불가능하다. 다음 구현은 기존 게임에서 실제 CD 읽기가 성공하는 인터럽트 활성화 이후 호출 지점을 찾아 로더를 한 번만 실행해야 한다.
