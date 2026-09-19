# MMR 이름설정 write-PC 추적 프로토콜

선행:
1. 일본판 원본 WRAM differential Experiment A/B
2. mmr_name_entry_wram_diff.py
3. 필요 시 mmr_name_entry_wram_stride.py

그 결과의 strong field만 대상으로 한다.

## 프로브 생성

python tools/mmr_name_entry_generate_write_pc_probe.py slot1_report.json -o name_write_probe.lua

프로브는 후보 WRAM field에 대한 WRITE callback만 건다.
ROM/RAM 값을 변경하지 않는다.

## 독립 로그

같은 첫 이름 칸에서 최소 3개의 서로 다른 일본어 문자를 사용한다.

각 문자마다:
- 같은 초기 상태에서 시작
- 프로브 실행
- 한 글자 입력
- 즉시 로그 저장

예:
charA.log
charB.log
charC.log

## 파싱

python tools/mmr_name_entry_parse_write_pc_logs.py ^
  --log charA=charA.log ^
  --log charB=charB.log ^
  --log charC=charC.log ^
  -o write_pc_report.json

같은 후보 field에 같은 PC가 3개 독립 로그에서 반복되면
NAME_ENTRY_WRITE_PC_CANDIDATES.

이것도 아직 이름 버퍼 확정이 아니다.

다음:
- 해당 PC의 bounded exec trace
- 선택 테이블 read -> 변환 -> WRAM write dataflow 확인
- slot1/slot2 address stride 확인
- delete/complete/cancel
- save/reset/load

그 뒤에만 physical binding contract로 승격한다.
