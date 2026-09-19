# MMR 이름설정 원본/한글판 5행 geometry 캡처 프로토콜

목적: 이름설정 커서가 위/아래 행 글자에 걸리는 문제를 수치로 차단한다.

## 입력

일본판 원본과 동일 후보 SHA의 한글판에서 각각 같은 페이지/같은 화면 상태로 5장을 캡처한다.

각 세트:
- row1.png : 커서 1행
- row2.png : 커서 2행
- row3.png : 커서 3행
- row4.png : 커서 4행
- row5.png : 커서 5행

다른 애니메이션/메시지/페이지 전환이 섞이지 않게 한다.

## 분석

tools/mmr_name_entry_geometry_compare.py

예:
python tools/mmr_name_entry_geometry_compare.py ^
  --original captures/jp ^
  --candidate captures/kr ^
  --crop X,Y,W,H ^
  --out work/name_geometry

5장을 median 합성해서 커서 없는 정적 화면을 재구성하고 각 캡처와의 diff로 커서 bbox를 찾는다.

측정:
- 커서 Y 중심
- 1→5행 Y step
- 커서 높이/폭
- 정적 글자 행별 visible bbox
- 인접행 visible glyph와 커서 bbox의 세로 겹침 px
- 원본 대비 이름 글자 visible height
- 원본 대비 커서 높이와 Y step

## HARD PASS

- candidate max_adjacent_row_overlap_px = 0
- 5행 Y step 내부 편차 <= 1px
- 원본 대비 Y step 차이 <= 1px
- 원본 대비 커서 높이 차이 <= 1px
- 원본 대비 이름 글자 visible height 차이 <= 2px
- 모든 캡처는 같은 후보 SHA

폰트를 움직여 커서 문제를 숨기면 안 된다.
폰트 visible bbox와 cursor geometry를 별도 계약으로 고친다.

## 현재 상태

원본 실제 캡처는 아직 회수되지 않았으므로 수치 미확정.
구형 이름 인계서의 12x12은 논리/임시 글리프 기준이며 실제 셀 스텝·행간·커서 사각형은 원판 측정 전 미확정이었다.
사용자 실화면 관찰에 따라 이름 폰트는 대사 폰트와 분리해 Mona10 계열을 1순위 후보로 사용한다.
