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

## Priority change

The previous distribution failures were mainly SYSTEM/UI, with NAME ENTRY considered fatal.

Current order:
1. name-entry original behavior/font/cursor/binding closure
2. system/UI surface inventory and runtime regression
3. font family finalization
4. Japanese-original dialogue review
5. full language/art sweep
6. release promotion

Dialogue polish must not outrank SYSTEM/UI blockers.

## Name-entry font policy

Old 12x12 name-entry assumption is superseded.

Retained:
- logical 200 unique Hangul syllables
- 4 pages x 50
- 10 columns x 5 rows logical layout

Superseded:
- physical name-entry glyph size = dialogue 12x12

Current primary candidate:
- MMR Mona10 Name Custom v0.2
- Mona10 Regular native 10px
- neutral raster candidate 10x12
- actual current 200-char visible body mostly 8..9 px
- no geometric scaling
- separate from dialogue Mona12

Static status:
- 200 unique logical chars
- all 200 inside KS2350
- char -> KS2350 ID -> 08 hi lo -> same char: 200/200 PASS
- blank 0 / clipping 0 / duplicate bitmap 0
- v0.2 reduces <=2-pixel confusable set to two review pairs
- remaining visual pairs stay review-only; do not distort them blindly

Critical sentinels:
- 한 ID2210 / 08 0E E2
- 힌 ID2344 / 08 0F C8
- 이 ID1547 / 08 0A CB
- 히 ID2342 / 08 0F C6

If runtime intended 한 renders/inputs as 힌 or 이, classify mapping/page/index/runtime binding first, not font art.

## New NAME ENTRY hard gates

### 1. Original comparison
qa/MMR_NAME_ENTRY_ORIGINAL_COMPARE_TEMPLATE.json

Requires JP original vs same candidate SHA for:
- visible font size/bbox
- baseline/top-bottom margins
- cursor row step / box height / target alignment
- adjacent row overlap
- input/delete/cancel/complete
- max length / over-limit
- save/reset/load
- consumers and state after exit

### 2. Automatic 5-row geometry
tools/mmr_name_entry_geometry_compare.py

Input:
- JP original row1..row5 PNG
- KR candidate row1..row5 PNG
- tight grid crop
- exact candidate SHA

Hard:
- adjacent-row overlap = 0 px
- row step stable
- candidate row step matches original within tolerance
- cursor height matches original
- name visible height matches original class

Capture PNG SHA256s are recorded in report.

### 3. Static ROM page binding
tools/mmr_name_entry_rom_binding_gate.py

Builds exact expected 4 pages from the 200 logical chars as private08 tokens.
Requires each 50-entry / 150-byte page payload to occur exactly once in the exact candidate ROM.

PASS proves page payload existence/identity only.
Runtime cursor/index -> page selection still requires runtime evidence.

### 4. Runtime identity
Every visible cell:
screen cell -> displayed char -> selected char -> committed name
must match.
Particular sentinels 한/힌/이/히 mandatory.

## System/UI font families

qa/MMR_UI_FONT_SURFACE_MATRIX_V1.json

P0 surfaces:
- MEMORY_CENTER_NOTICE
- RECORD_SELECTION
- NAME_ENTRY
- MAIN_MENU
- ITEM_EQUIPMENT_STATUS
- SHOP_SERVICE_UI
- BATTLE_UI
- SAVE_LOAD_UI

Rules:
- do not reuse dialogue Mona12 automatically
- do not reuse name Mona10 automatically
- measure original visible height/baseline/row pitch first
- different renderer/state routes remain separate until proven shared

Generic fixed-text compare:
tools/mmr_ui_surface_compare.py

It compares original/candidate text-only crops for:
- visible height
- top anchor
- crop overflow
- size class
and binds evidence to candidate SHA.

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

Current V4 hard requirements include:
- exact parent
- name-entry JP original compare
- automatic name-entry geometry PASS
- exact 4-page ROM binding PASS
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
3. Read latest local handoff/status and prove Stage1467 parent SHA.
4. Locate actual Stage1467 name-entry page tables and cursor code/state route.
5. Run mmr_name_entry_rom_binding_gate.py on Stage1467.
   - If FAIL: fix page data/binding before font art.
6. Capture JP original name entry rows 1..5.
7. Capture same Stage1467/child candidate rows 1..5.
8. Run automatic geometry compare.
9. Apply Mona10 Name Custom v0.2 to the verified name-entry font path only.
10. Fix cursor Y step/box/anchor independently so adjacent overlap is 0.
11. Re-run page identity, all 4 pages, 200 visible cell selections, max length, save/reset/load.
12. Classify remaining P0 system/UI surfaces with UI surface compare.
13. Only after P0 SYSTEM/UI PASS, resume dialogue font/translation integration.
14. Do not call build RC/final until release promotion gate returns RELEASE_ALLOWED.

## Current boundary

Codex/DevSpace is not exposed in this chat, so:
- no local H: write is claimed
- no new candidate ROM is claimed
- no new REAL Mesen runtime result is claimed
- all new work here is static/offline tooling and fail-closed QA preparation

NO_NEW_REAL.
