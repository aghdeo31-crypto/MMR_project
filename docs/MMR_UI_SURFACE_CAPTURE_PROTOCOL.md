# MMR 시스템/UI 원본 비교 캡처 프로토콜

이름설정 커서는 별도 5행 geometry 도구를 사용한다.
그 외 고정 시스템/UI 글자는 tools/mmr_ui_surface_compare.py 로 비교한다.

## 대상 P0 surface
- MEMORY_CENTER_NOTICE
- RECORD_SELECTION
- MAIN_MENU
- ITEM_EQUIPMENT_STATUS
- SHOP_SERVICE_UI
- BATTLE_UI
- SAVE_LOAD_UI

각 surface에서 일본판 원본과 동일 후보 SHA 한글판을 같은 화면 상태로 캡처한다.

manifest 예:
{
  "regions": [
    {
      "id": "TITLE_LINE",
      "crop": [40, 60, 160, 16],
      "threshold": 18,
      "height_tolerance_px": 2,
      "anchor_tolerance_px": 2
    }
  ]
}

crop은 창 테두리/아이콘/커서를 피하고 텍스트 영역만 잡는다.

PASS:
- 원본/후보 nonempty
- 후보 글자가 crop 경계에 닿지 않음
- visible height 원본 대비 허용범위
- 상단 anchor/baseline 원본 대비 허용범위

이 결과와 renderer/state route를 함께 기록해 실제 폰트 패밀리를 확정한다.
