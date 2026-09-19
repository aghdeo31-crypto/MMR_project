# MMR Stage1468 — SYSTEM/UI + NAME ENTRY PRIORITY handoff

Date: 2026-09-19 KST
Status: OFFLINE_PREP / RELEASE HOLD / NO_NEW_REAL

## Parent authority

Stage1467 RC2_TEST remains the parent until local workspace proves otherwise.

Expected parent ROM:
- Metal_Max_Returns_Korean_RC2_TEST_20260918.sfc
- SHA256 29EBF0A5DAB0A646FF9AF6E68127AAE6C8182AB2129C2819FB37177A94453BEB

Japanese original authority:
- Metal Max Returns (Japan).sfc
- size 4,194,304
- CRC32 4396A35B
- SHA256 6a68e1806d8d72accb4a5218330210e178880216863c1c38b8865032c5c28724

No release promotion is allowed from a different parent/candidate SHA.

## Priority

1. name-entry original behavior/font/cursor/binding closure
2. system/UI surface inventory and regression
3. font-family finalization
4. Japanese-original dialogue review
5. full language/art sweep
6. release promotion

Dialogue polish must not outrank SYSTEM/UI blockers.

## Name-entry font

Old physical 12x12 name-entry assumption is superseded.

Retained:
- 200 unique logical Hangul syllables
- 4 pages x 50
- 10 columns x 5 rows

Primary physical-font candidate:
- MMR Mona10 Name Custom v0.2
- Mona10 Regular native 10px
- neutral raster candidate 10x12
- current 200-char visible bodies mostly 8..9px
- no geometric scaling
- separate from dialogue Mona12

Static:
- 200/200 chars unique and inside KS2350
- char -> KS2350 ID -> 08 hi lo -> same char = 200/200 PASS
- blank 0 / clipped 0 / duplicate bitmap 0
- <=2px confusable set reduced to two review-only pairs
- 한/힌/이/히 remain runtime/mapping sentinels, not art-similarity suspects

Sentinels:
- 한 ID2210 / 08 0E E2
- 힌 ID2344 / 08 0F C8
- 이 ID1547 / 08 0A CB
- 히 ID2342 / 08 0F C6

## Name-entry hard gates

### A. Japanese-original comparison
qa/MMR_NAME_ENTRY_ORIGINAL_COMPARE_TEMPLATE.json

Covers:
- font visible bbox/size relation to dialogue
- baseline/top-bottom margins
- cursor row step/box/anchor
- adjacent-row overlap
- input/delete/cancel/complete
- max length/over-limit
- save/reset/load
- consumer displays and state after exit

### B. Automatic five-row geometry
tools/mmr_name_entry_geometry_compare.py

Current V3:
- JP original row1..row5 PNG
- KR candidate row1..row5 PNG
- exact Japanese ROM SHA pinned
- exact candidate SHA mandatory
- all ten capture SHA256s recorded

Hard:
- candidate adjacent-row overlap = 0px
- five-row Y step stable
- original/candidate row step match within tolerance
- cursor height match within tolerance
- visible name-font height match within tolerance

Commits:
- auto screenshot upgrade 42bf7058a5cd3aa3e546b1e25655e0554f824947
- capture/ROM SHA evidence binding e8061e169238ef577a4c06ef4caf326efcfa3dd1
- capture protocol 53387ad6b854572ddcb31d887476f5da30d2679d
- selftest ab02d4102760bf31d216eb94b5f1765d0f653619

### C. Exact ROM page binding
tools/mmr_name_entry_rom_binding_gate.py

Expected payload:
- page 1: 50 chars / 150 bytes
- page 2: 50 chars / 150 bytes
- page 3: 50 chars / 150 bytes
- page 4: 50 chars / 150 bytes
- encoding: private08 08 hi lo in KS2350 ID order

Static PASS requires each page byte sequence exactly once in exact candidate ROM.
Runtime cursor/index -> table selection remains a separate runtime requirement.

Commits:
- gate 0219d69193e5445044c35d27c2246d246afe02fd
- selftest c3e3c884f02a40c4787f24a14923a407d88d0a89

### D. Runtime identity
Every cell:
screen logical cell -> visible glyph -> selected glyph -> committed name
must match.

All 200 cells required; 한/힌/이/히 are mandatory sentinels.

## System/UI font-family inventory

qa/MMR_UI_FONT_SURFACE_MATRIX_V1.json
commit 09f4375ce8aa82e11f83b3ed6cc1e9b84502b7c8

P0:
- MEMORY_CENTER_NOTICE
- RECORD_SELECTION
- NAME_ENTRY
- MAIN_MENU
- ITEM_EQUIPMENT_STATUS
- SHOP_SERVICE_UI
- BATTLE_UI
- SAVE_LOAD_UI

Rules:
- no automatic Mona12 reuse
- no automatic Mona10 reuse
- original visible height/baseline/row pitch first
- renderer/state route remains separate until proven shared

Generic fixed-text comparator:
- tools/mmr_ui_surface_compare.py
- commit a27d5433d7d08f246f1bcb590c8da05b219dfce4
- selftest cc69314ad3db88ab37f4ee1406c5501a6c875def
- capture protocol 6dbbb396e3682a6d6354afdb38e6547f1ca89b9f

Measures:
- visible height
- top anchor
- crop overflow
- size class
and binds PNG/manifest evidence to candidate SHA.

## Chained SYSTEM/UI preflight

scripts/RUN_STAGE1468_SYSTEM_UI_PREFLIGHT.ps1
commit 39096e5bb14a75e2a071e30d8f8c381d680537b7

Required input:
- exact candidate ROM + expected SHA
- JP original name row1..row5 captures
- candidate name row1..row5 captures
- name-grid crop
- seven-surface P0 UI capture plan

Runs in fail-closed order:
1. KS2350 glyph identity
2. exact four-page name ROM binding
3. name-entry original-vs-candidate five-row geometry
4. seven fixed P0 system/UI surface compares

PASS classification:
PASS_STAGE1468_SYSTEM_UI_PREFLIGHT

Even PASS only allows a RUNTIME TEST candidate.
It never allows RC/final directly.

Capture plan:
- qa/MMR_STAGE1468_P0_UI_CAPTURE_PLAN_TEMPLATE.json
- commit 723414581a8167f0a38b080f14d794c9e5d53c86

Preflight contract:
- qa/MMR_STAGE1468_SYSTEM_UI_PREFLIGHT_SELFTEST.json
- commit 06bbf67391ee6e81ff60c0fb0221ddf17ca9c1ec

## Dialogue font

Dialogue primary candidate remains MMR Mona12 Custom.
Do not integrate into a release candidate until name-entry/system/UI blockers are closed.

## Translation authority

Japanese original is top authority.
English translation is auxiliary only.
No English offsets/order as Japanese record binding.
No semantic shortening to avoid missing glyphs.

## Release promotion

tools/mmr_release_promotion_gate.py

Current V4:
MMR_THIRD_ATTEMPT_RELEASE_PROMOTION_V4_NAME_BINDING_LOCKED
commit 9f3d2c1404c7f2a4c51e6d776c50056e12a23155

Hard requirements include:
- exact parent
- name-entry JP original compare
- automatic name-entry geometry PASS / adjacent overlap 0
- exact four-page ROM binding PASS
- glyph identity
- font structure/art/small-font family
- Japanese-original translation gate
- static binary diff
- critical system/UI/name-entry runtime matrix
- full runtime matrix
- language/art sweep

One exact candidate SHA only.
No evidence mixing across builds.

## Exact restart when Codex/DevSpace returns

1. Open H:\한글화\MMR_Project writable checkout.
2. git status --short.
3. Read latest local handoff/status and prove exact Stage1467 parent SHA.
4. Locate actual Stage1467 name-entry page tables + cursor/state route; do not guess addresses.
5. Run name-entry ROM binding gate on Stage1467/child.
   - If FAIL: fix page payload/binding before font art.
6. Capture Japanese-original name rows 1..5.
7. Capture same candidate SHA name rows 1..5.
8. Run automatic geometry compare.
9. Bind Mona10 Name Custom v0.2 only to verified name-entry font route.
10. Fix cursor Y step/box/anchor separately; adjacent overlap must be 0.
11. Re-run all four pages, 200 cell identity, max length, save/reset/load.
12. Capture seven P0 fixed system/UI surfaces in JP/KR.
13. Run RUN_STAGE1468_SYSTEM_UI_PREFLIGHT.ps1.
14. Only after SYSTEM/UI preflight PASS, continue dialogue font/JP-original translation integration.
15. RC/final remains forbidden until release promotion gate returns RELEASE_ALLOWED.

## Current boundary

Codex/DevSpace is not exposed in this chat.
Latest File Library search did not recover the physical Stage1467 name-entry page/cursor source, so no code address is fabricated.

Therefore:
- no local H: write claimed
- no new candidate ROM claimed
- no new REAL Mesen result claimed
- all new work is static/offline tooling and fail-closed QA preparation

NO_NEW_REAL.
