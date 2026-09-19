# MMR 이름설정 원본 비교 QA — 필수 절차

기준 일본판:
- Metal Max Returns (Japan).sfc
- size 4,194,304
- CRC32 4396A35B
- SHA256 6a68e1806d8d72accb4a5218330210e178880216863c1c38b8865032c5c28724

## 원칙

이름설정은 한글판만 정상 동작한다고 PASS하지 않는다.

일본판 원본과 후보 ROM을 같은 진입점에서 비교하고 다음 세 종류로 분류한다.

1. MUST_MATCH
   - 입력/삭제/취소/완료 의미
   - 빈 이름 처리
   - 최대 길이와 초과 입력 동작
   - 저장/로드 의미
   - 종료 후 상태
2. INTENTIONAL_KR_DIFFERENCE
   - 한글 4페이지 문자표
   - 한글 글리프 배열
   - 필요 시 페이지 전환 입력
   차이는 허용하지만 원본의 이름 버퍼/세이브/커서 안전 계약을 깨면 안 된다.
3. MUST_MATCH_OR_DOCUMENT
   - 원본 커서 wrap/초기화 등 UI 행동
   한글판에서 바뀐다면 바뀐 이유와 안전성을 증명해야 한다.

## 캡처 페어

각 항목은 반드시 같은 동작 지점의 두 캡처를 남긴다.

- JP_ORIGINAL_<id>.png
- KR_CANDIDATE_<id>.png

동작 상태가 중요한 항목은 스크린샷만으로 PASS하지 말고 로그/메모리 상태를 같이 기록한다.

특히:
- 페이지 전환 직전/직후 cursor index
- selected glyph code/ID
- name-buffer write address and before/after bytes
- complete/cancel branch
- save write bytes
- reset/load 후 복원 bytes
- exit 후 page/font/KMODE/source state

## 치명적 판정

다음 중 하나라도 있으면 이름설정 전체 FAIL:
- 화면 글자와 실제 입력 글자가 다름
- 원본에서는 유효한 입력이 후보에서 freeze/crash
- 최대 길이에서 오버런
- 취소/완료 의미가 원본과 달라짐
- 저장 후 이름이 변함
- 이름설정 종료 후 다른 UI가 깨짐
- 페이지 상태가 다음 시스템 화면에 잔류
- 원본 비교자료가 없음

## 배포 규칙

MMR_NAME_ENTRY_ORIGINAL_COMPARE_V1의 모든 항목이 PASS가 되기 전에는
NAME_ENTRY_CRITICAL = PASS로 승격하지 않는다.

그리고 NAME_ENTRY_CRITICAL이 PASS가 아니면 RC/final 패키지 생성 금지.
