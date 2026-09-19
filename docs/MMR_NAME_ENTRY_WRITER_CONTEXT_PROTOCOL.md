# MMR 이름설정 writer context 단계

선행:
- WRAM differential
- slot1/slot2 stride 후보
- write-PC parser에서 NAME_ENTRY_WRITE_PC_CANDIDATES

## context probe

mmr_name_entry_generate_writer_context_probe.py가 가장 강한 writer PC 하나를 고른다.

생성 Lua는 writer PC 실행 시:
- A/X/Y/S/D/DB/P/E
- PC 주변 48바이트
- native-stack 해석 32바이트
- emulation-stack page-1 해석 32바이트
- DP 주변 32바이트
를 로그한다.

모두 read-only.

## 검증

최소 3개 서로 다른 입력 문자 로그에서:
- 같은 writer PC
- 같은 48바이트 code window
- 각 로그에서 실제 hit
를 요구한다.

NAME_ENTRY_WRITER_CONTEXT_CANDIDATE는 writer 문맥을 고정할 뿐,
아직 이름 버퍼/코드 의미를 증명하지 않는다.

그 다음:
1. mode-aware 65C816 disassembly
2. writer 전 source/table read 역추적
3. slot1/slot2 physical code 대응
4. delete/complete/cancel
5. save/reset/load
