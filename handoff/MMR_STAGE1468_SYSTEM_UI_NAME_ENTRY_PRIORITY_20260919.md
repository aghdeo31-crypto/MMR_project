# MMR Stage1468 — SYSTEM/UI + NAME ENTRY PRIORITY handoff v2

Date: 2026-09-19 KST
Status: OFFLINE_PREP / RELEASE HOLD / NO_NEW_REAL

## Parent authority

Stage1467 RC2_TEST remains the parent until local workspace proves otherwise.

Expected parent ROM:
- Metal_Max_Returns_Korean_RC2_TEST_20260918.sfc
- SHA256 29EBF0A5DAB0A646FF9AF6E68127AAE6C8182AB2129C2819FB37177A94453BEB

Japanese original:
- Metal Max Returns (Japan).sfc
- 4,194,304 bytes
- CRC32 4396A35B
- SHA256 6a68e1806d8d72accb4a5218330210e178880216863c1c38b8865032c5c28724

No evidence mixing across candidate SHA.

## Priority

1. NAME ENTRY physical contract + original geometry
2. SYSTEM/UI P0 surfaces
3. small-font family closure
4. dialogue Mona12 integration
5. Japanese-original dialogue audit
6. full runtime / language sweep
7. release

## Corrected name-entry authority model

Historical MMR handoff explicitly states that these remain unresolved until Japanese-original tracing:
- physical name code width
- selectable code count/control range
- name buffer format/length
- terminator/space/empty-name contract
- save data name representation
- name-entry font address/compression/tile path
- physical cell step and cursor geometry
- whether every name consumer shares one renderer

Therefore:

FORBIDDEN assumptions:
- logical index 0..199 == physical code 00..C7
- dialogue KS2350/private08 token == name-entry code
- 1-byte or 2-byte name storage by guess
- English-patch name table == Japanese authority

### private08 probe status

tools/mmr_name_entry_rom_binding_gate.py is now PROBE ONLY.

It may search for a possible 08 hi lo page payload, but:
- absence is not a failure;
- a hit is not authority;
- release/preflight does not depend on it unless independent tracing proves that is the actual name-entry encoding.

Status:
- status/MMR_NAME_ENTRY_PRIVATE08_PROBE_STATUS.json
- commit c9fc9f1ee3eccd97494b0cc2c17af07a8b74be0b

## Format-agnostic physical binding gate

tools/mmr_name_entry_physical_binding_gate.py
latest commit 976da41ef71091a58e47fa1463bfee0a4db3a6cf

No encoding family is assumed.

### STATIC PASS
PASS_NAME_ENTRY_PHYSICAL_BINDING_STATIC requires:
- exact Japanese-original encoding/storage contract confirmed
- candidate SHA binding
- 200 logical cells -> 200 explicit physical code payloads
- all 200 roundtrip to intended chars
- control collision checked for all 200
- four page table witnesses tied to the real physical contract

STATIC PASS admits a runtime TEST candidate only.

### FULL PASS
PASS_NAME_ENTRY_PHYSICAL_BINDING_FULL additionally requires:
- selection -> name buffer path confirmed
- delete/complete/cancel semantics confirmed
- save -> reset -> load roundtrip confirmed
- runtime evidence attached

FULL PASS is required for release.

Template:
- qa/MMR_NAME_ENTRY_PHYSICAL_BINDING_TEMPLATE.json
- commit ef6ee2ab84fbc724ba7eac652647512415dbd5ea

## Name-entry font

Old physical 12x12 name-entry assumption is superseded by runtime observation that the name font is smaller than dialogue.

Primary candidate:
- MMR Mona10 Name Custom v0.2
- Mona10 Regular native 10px
- 10x12 neutral raster candidate
- body mostly 8..9px on current name table
- no geometric scaling
- separate from dialogue Mona12

Logical table:
- 200 unique syllables
- 4 x 50
- 10 x 5
- logical ordering remains valid
- physical mapping remains independently proven, never inferred

## Name-entry geometry

tools/mmr_name_entry_geometry_compare.py

Requires:
- JP original row1..row5 PNG
- candidate row1..row5 PNG
- exact candidate SHA
- Japanese original SHA pinned
- tight grid crop

Hard:
- adjacent-row visible-glyph overlap = 0 px
- row step stable
- original/candidate step matched
- cursor height matched
- name visible height matched within tolerance
- all ten capture SHA256s recorded

No font shifting to hide a cursor bug.

## System/UI compact font

Full-coverage compact candidate:
- MMR Mona10 UI Custom v0.2
- KS2350 2350/2350
- blank 0
- clip 0
- duplicate bitmap groups 0

Mona10-Bold rejected as primary:
- about +26.4% mean set-pixel density
- exact duplicate group exists: 틤 / 팀

Files:
- tools/mmr_mona10_ui_custom_v0_2.py
- qa/MMR_MONA10_UI_CUSTOM_V0_2_KS2350_QA.json
- status/MMR_SMALL_UI_FONT_CANDIDATE_STATUS_V1.json

Important:
full KS2350 coverage does NOT authorize the font on every UI surface.

## Actual P0 UI corpus gate

tools/mmr_small_ui_corpus_font_risk.py
commit 6441d72ab7c20713f65c831bab74ae3740a2de2d

Required P0 text ledger surfaces:
- MEMORY_CENTER_NOTICE
- RECORD_SELECTION
- MAIN_MENU
- ITEM_EQUIPMENT_STATUS
- SHOP_SERVICE_UI
- BATTLE_UI
- SAVE_LOAD_UI

Only exact project/runtime Korean UI strings are allowed in the ledger.
Do not invent missing strings.

The gate:
- extracts actual P0 Hangul usage
- verifies KS2350 coverage
- ranks close Mona10 v0.2 pairs
- prioritizes pairs used together on the same P0 surface

This prevents needless manual changes to unused KS2350 glyphs.

Template:
- qa/MMR_P0_UI_TEXT_LEDGER_TEMPLATE.tsv
- commit 2f6cca4bcfed546d7ae40c3af0127bef14a26ab4

## UI surface compare

tools/mmr_ui_surface_compare.py

P0 surfaces:
- Memory Center notice
- record selection
- main menu
- item/equipment/status
- shop/service UI
- battle UI
- save/load UI

Compare Japanese original vs exact candidate:
- visible font height
- top anchor/baseline class
- crop overflow
- size class
- screenshot/manifest SHA

Name-entry cursor motion remains a separate five-capture geometry gate.

## Stage1468 chained preflight v2

scripts/RUN_STAGE1468_SYSTEM_UI_PREFLIGHT.ps1
latest commit 3a6a048fc71d8b7ec509cecd1bb311d5a8a11c88

Mandatory:
1. exact candidate SHA
2. KS2350 identity
3. format-agnostic name-entry PHYSICAL BINDING STATIC PASS
4. original-vs-candidate five-row name geometry PASS
5. all seven fixed P0 system/UI surface comparisons PASS

Optional:
- private08 reconnaissance probe

Preflight PASS only allows runtime TEST.
It never means RC/final.

## Release promotion v5

tools/mmr_release_promotion_gate.py
latest commit f9313838a93f1a5caa5066d7e61d69e296e52c46

Release now requires:
- exact parent/candidate
- original-JP name comparison
- automatic name geometry PASS, adjacent overlap 0
- PHYSICAL BINDING FULL PASS
- glyph identity
- font structure/art
- small-font family complete
- Japanese-original translation gate
- binary diff
- critical SYSTEM/UI/NAME runtime
- full runtime matrix
- language/art sweep

No private08/1-byte/2-byte/dialogue-code assumption is accepted as name authority.

## Exact restart when Codex returns

1. Open H:\한글화\MMR_Project writable checkout.
2. git status --short.
3. Verify Stage1467 exact parent SHA.
4. Read current local latest handoff/status; do not resurrect superseded Stage.
5. Trace Japanese original name selection table -> physical selected code -> temporary name buffer.
6. Determine:
   - actual code width/format
   - page/table source
   - terminator/length/space
   - delete/complete/cancel
   - save copy/restore
7. Fill MMR_NAME_ENTRY_PHYSICAL_BINDING_TEMPLATE.json.
8. Require PHYSICAL BINDING STATIC PASS.
9. Capture Japanese and candidate row1..row5; require geometry PASS.
10. Bind Mona10 Name Custom only to proven name-entry font route.
11. Fix cursor geometry separately; adjacent overlap 0.
12. Run all 200 selections and save/reset/load; upgrade binding to FULL.
13. Recover exact P0 UI strings and fill P0 UI ledger.
14. Measure each original UI surface before choosing Mona10/Mona12/other size.
15. Run Stage1468 SYSTEM/UI preflight.
16. Only then integrate dialogue Mona12 and Japanese-original dialogue corrections.
17. Never label RC/final unless release promotion gate says RELEASE_ALLOWED.

## Current boundary

Codex/DevSpace is still absent from this chat.
Latest File Library search did not recover the physical Stage1467 name-table/cursor source.

Therefore:
- no local H: write claimed
- no new ROM claimed
- no REAL runtime result claimed
- new work remains fail-closed static/offline preparation

NO_NEW_REAL.
