# MMR 폰트 패밀리 분리 정책 v1 — 시스템/UI 우선

이번 세 번째 배포 준비에서는 폰트를 하나로 통일하지 않는다.

## 현재 확정/후보

### 대사
- Mona12 Regular 기반 MMR Custom
- 12px / 12x12 계열
- 대사와 큰 시스템 문구에서만 사용 가능
- 다른 UI에 자동 재사용 금지

### 이름설정
- Mona10 Regular 기반 MMR Name Custom v0.2
- native 10px
- 10x12는 래스터 후보일 뿐 실제 셀 크기 주장이 아님
- 실제 몸체는 현재 200자에서 주로 8~9px 높이
- 커서/행간은 일본판 원본 별도 측정

## 시스템/UI

다음 화면을 각각 독립 surface로 측정한다.
1. 메모리센터 안내문
2. 기록 선택
3. 메인 메뉴
4. 아이템/장비/상태
5. 상점/서비스
6. 전투 UI
7. 세이브/로드
8. 이름설정
9. 대사

각 surface에서 기록:
- 원본 visible glyph 높이/폭 범위
- 원본 baseline/top/bottom margin
- 행 pitch
- 커서/선택 강조와의 관계
- 같은 renderer/font state를 쓰는지
- 후보 한글 폰트
- runtime capture PASS 여부

## 금지

- 대사 12x12을 축소해서 소형 UI에 재사용
- 이름설정 Mona10을 다른 UI에 근거 없이 재사용
- 원본보다 큰 글자를 넣고 창 크기/커서를 억지로 늘려 해결
- 서로 다른 renderer인데 같은 폰트 계약이라고 가정
- 한 화면만 보고 전체 시스템/UI PASS 처리

## 배포 조건

P0 시스템/UI surface가 모두 원본 대비 분류되고 동일 후보 SHA에서 런타임 PASS하기 전에는 small_font_family_complete=false.

특히 이름설정은 별도 fatal gate이며:
- 원본 이름 글자 크기
- 5행 커서 geometry
- 200자 선택 identity
- 저장/로드
를 모두 통과해야 한다.
