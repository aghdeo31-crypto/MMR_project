# MMR 이름설정 물리 버퍼 탐색 — WRAM differential 프로토콜

목적:
이름 코드 폭/형식을 추측하지 않고 일본판 원본 런타임에서 직접 좁힌다.

## Experiment A — 첫 번째 이름 칸

정확한 일본판 ROM의 같은 이름설정 초기 상태를 사용한다.

1. empty.bin
   - 이름 버퍼 비어 있음
   - 첫 번째 입력 위치
2. a.bin
   - 일본어 문자 A 하나만 첫 칸에 입력
3. b.bin
   - 초기 상태로 복구한 뒤 다른 문자 B 하나만 첫 칸에 입력
4. c.bin
   - 초기 상태로 복구한 뒤 다른 문자 C 하나만 첫 칸에 입력
5. delete.bin
   - A 하나 입력 후 삭제해서 빈 상태로 되돌린 상태

모든 파일은 같은 WRAM 범위를 덤프한다. 권장: 7E:0000-7F:FFFF 전체.

mmr_name_entry_wram_diff.py가 다음 후보를 우선한다:
- A/B/C 모두 base와 달라짐
- A/B/C 값이 서로 다름
- delete에서 base로 복귀
- 1~4바이트 compact field
- 주변 대량 volatile block이 아님

이 결과만으로 이름 버퍼라고 확정하지 않는다.

## Experiment B — 두 번째 이름 칸

고정된 동일 첫 글자를 입력한 상태를 공통 base로 만든다.
그 다음 두 번째 칸에 서로 다른 A/B/C 문자를 각각 입력해서 위 실험을 반복한다.

mmr_name_entry_wram_stride.py로 Experiment A/B 보고서를 교차한다.

강한 후보:
- 같은 field 폭
- slot2 주소 = slot1 주소 + field 폭
- A/B/C 값 다양성 패턴 일치
- 양쪽 delete 복귀

그래도 encoding은 아직 확정하지 않는다.

## Authority 승격에 추가로 필요한 것

1. 후보 주소 write callback에서 실제 write PC 확보
2. 같은 PC/경로가 이름 선택 확정 때 반복되는지 확인
3. 화면 선택 문자와 후보 field 값 3개 이상 대응
4. 삭제/완료 의미 확인
5. save -> reset -> load에서 같은 이름 의미가 복구
6. 그 뒤에만 MMR_NAME_ENTRY_PHYSICAL_BINDING_TEMPLATE.json 작성

본문 대사용 private08/KS2350 ID를 이름 코드로 가정하지 않는다.
