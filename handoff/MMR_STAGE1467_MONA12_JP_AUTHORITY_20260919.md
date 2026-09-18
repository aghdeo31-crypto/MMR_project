# MMR Stage1467 후속 — Mona12 전환 / 일본어 원문 Authority

작성: 2026-09-19 KST

## 최신 검증 기준선
- Stage1459 RC1은 공유 경로 오염으로 폐기/HOLD.
- 원인: Stage1427 `FD:9398` 후처리가 이름입력 전용 F4 source-bank를 공유 경로까지 강제하여 정상 `7E:007E`가 `F4:007E`로 변함.
- Stage1467 `RC2_TEST`에서 F4 적용을 이름입력 컨텍스트로 gate하고 `FD:9512~9535` 디렉터리 변경을 분리.
- 확인: 메모리센터 안내문 Stage1415 대비 pixel diff 0, 신규게임 fatal 0, 이름입력 4페이지/저장 PASS, target5 PASS, 38/38 회귀 PASS, status16/field6 lifetime PASS.

## 번역 Authority
1. 일본어 원문이 최상위 번역 Authority.
2. 기존 한글문과 향후 수정문은 일본어 원문과 직접 대조.
3. 영어판은 보조 참고만 사용.
4. 글리프/폭 문제로 원문 의미·뉘앙스·고유명사·말투를 줄이거나 영어식으로 우회하지 않음.
5. 제어 토큰/렌더러 상태와 번역 의미를 분리해 QA.

## Mona12
- 사용자 제공 Mona12.zip 기준.
- 12px 렌더에서 한글 11,172자 모두 12×12 셀 overflow 0 / missing 0.
- Mona12.ttf와 Mona12TextKR.ttf의 한글 11,172자 12px 비트맵은 동일.
- Bold는 Regular보다 픽셀 밀도가 높아 CRT/실기에서 뭉침 위험이 커서 우선 후보는 Mona12 Regular.
- 폰트 원본은 저장소에 재배포하지 않고 기존 MMR 슬롯/packer 입력 비트맵만 빌드 시 생성.
- Stage1467 안정화 수정과 폰트 교체를 한 패치로 섞지 않음.

## 다음 순서
1. Stage1467 exact ROM/source/packer SHA lineage 확인.
2. 기존 font-slot/packing 규칙 유지 + Mona12 Regular bitmap만 교체한 FONT_ONLY 후보.
3. Stage1467 대비 code/pointer/context byte 동일, font payload만 변경됐는지 diff gate.
4. 회귀: 메모리센터 안내문, 신규게임 기록 선택, 이름입력 4페이지+저장, target5, 38/38, status16/field6 lifetime.
5. 일본어 원문↔한글문 전수 대조 후 미번역/오역/어투/고유명사 수정.
6. 필요한 글리프는 Mona12에서 생성. 의미 축약 금지.

## 금지
- Stage1459 RC1의 공유 F4 강제 로직 재도입 금지.
- 영어판 row offset/pointer/table ordering을 일본판 binding Authority로 사용 금지.
- source token 0x58 재사용/탈취 금지.
