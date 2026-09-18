# MMR Stage1468 PREP — Mona12 FONT_ONLY + JP-original review authority

- Date: 2026-09-19 KST
- Scope: OFFLINE_PREP_NO_ROM_WRITE
- Parent runtime/binary authority: local project Stage1467 RC2_TEST (not materialized in this chat)
- New REAL runtime evidence: NO_NEW_REAL
- ROM/IPS write in this prep: NONE

## 1. Preserve Stage1467 before font work

Do not mix the Mona12 migration with the Stage1467 runtime fixes.
The font candidate must be derived as a FONT_ONLY child.

Required first local checks when Codex/DevSpace returns:
1. read latest local handoff/status/Stage1467 artifacts;
2. freeze exact Stage1467 ROM/source/packer SHA256;
3. identify the current font-slot and packing ranges from that authority;
4. run FONT_ONLY diff gate after candidate generation;
5. reject any code/pointer/context write outside approved font ranges.

## 2. Mona12 decision

Primary candidate: Mona12 Regular, 12 px, 12x12 cell, draw y=-1.

Exhaustive Hangul QA (U+AC00..U+D7A3, 11,172 glyphs):
- missing: 0
- clipping at y=-1: 0
- width: 10..11 px
- height: 10..11 px
- mean pixels Regular: 49.363856...
- mean pixels Bold: 62.889008...
- Bold/Regular density ratio: 1.27398897...
- Regular vs Bold bitmap differences: 11,172 / 11,172
- Mona12 vs Mona12TextKR bitmap differences: 0 / 11,172

Vertical scan:
- y=-3: 11,172 clipped
- y=-2: 11,172 clipped
- y=-1: 0 clipped (selected)
- y=0: 0 clipped
- y=1: 11,115 clipped

Generated neutral source artifact (not ROM packing):
- mona12_regular_12x12_row16be.srcbin
- bytes: 268,128
- SHA256: 10ee1bf385873fd6ba127485798b08de0ff6b5cb647c89eac64bd95e0a3c2a24
- format: 12 rows/glyph x BE16 row, upper 12 bits used
- IMPORTANT: this is only a neutral raster source; Stage1467 packer/layout remains authority.

Font input:
- Mona12.ttf SHA256: b305cc135d9fc543792f7591dc9008a82e8cf1c9e6a4ed2127745e2924d000c1
- font file itself is not stored in this repository.

## 3. Translation authority rule

New policy from user:
- Japanese original is the top translation authority.
- Existing Korean and every future edit are checked directly against Japanese.
- English translation is auxiliary reference only.
- Do not shorten/alter Japanese meaning because of glyph/UI width pressure.
- If a needed glyph is missing, make the glyph rather than rewrite around it.

Historical provenance retained:
- Stage439 FINAL translation: IDs 0..3340 / 3341 rows.
- safe JP-binding authority removed English-ROM offset/pointer/table columns.
- do not resurrect English row ordering as Japanese record binding evidence.

New gate:
tools/mmr_jp_translation_review_gate.py
- EDIT requires non-empty Japanese original text;
- EDIT requires an approved exact-JP evidence type;
- ENGLISH/ENGLISH_ONLY is never sufficient authority;
- Korean before/after explicit control-token sequence must remain identical;
- optional control signatures must remain identical;
- PASS is provenance/control safety only, not semantic certification or ROM binding.

## 4. Files/commits created in this prep

- handoff/MMR_STAGE1467_MONA12_JP_AUTHORITY_20260919.md
  commit 12735cd0b76eaabb024222c472bec28dd3af99ca
- tools/mmr_mona12_source_builder.py
  commit 3d98b96454568168549f9813b5f823adbe18fdfa
- qa/MMR_MONA12_12X12_SOURCE_REPORT.json
  commit 2ea49fe2072722505fac49c30204916d05c7e316
- tools/mmr_font_only_diff_gate.py
  commit c3e68aa3f245c7448b6f7dbd3bdf7a40a6cb8c4b
- qa/MMR_MONA12_REGULAR_BOLD_QA.json
  commit 7267acbe524beae7b6deab49576381655b48d3c9
- qa/MMR_MONA12_VERTICAL_ALIGNMENT_QA.json
  commit e34e0523844958c4f0d3495b246538f049fc3a48
- tools/mmr_jp_translation_review_gate.py
  commit 99bea046cdcdc3da4cae2a0098b102f49ded99fa

## 5. Exact restart sequence

When writable Codex returns:
1. H:\한글화\MMR_Project checkout / git status.
2. Read current local handoff/status and verify Stage1467 is still authority.
3. Hash exact Stage1467 ROM/source/packer inputs.
4. Locate existing Korean font slot map / glyph map / packer.
5. Feed Mona12 Regular rasters through the EXISTING packer, not the neutral row16be format directly.
6. Build Stage1468_FONT_ONLY candidate.
7. Run mmr_font_only_diff_gate.py using actual Stage1467 font ranges.
8. Required regression:
   - Memory Center notice exact display
   - record selection no freeze
   - new game path no fatal
   - name entry 4 pages + save
   - target5
   - existing 38/38 regression
   - status16/field6 lifetime
9. After FONT_ONLY is stable, resume Japanese-original dialogue audit.
10. Every dialogue EDIT must pass mmr_jp_translation_review_gate.py.

## Classification

CONFIRMED:
- Mona12 Regular 12px can raster all 11,172 modern Hangul syllables into 12x12 with zero clipping at y=-1.
- Bold is materially denser (+27.4% mean set pixels), so not the first candidate.
- Mona12TextKR gives no Hangul bitmap benefit at 12px over Mona12.
- JP-original translation authority policy is encoded in a fail-closed review gate.

OPEN:
- exact Stage1467 current local SHA/packer/font ranges (Codex unavailable in this chat);
- actual FONT_ONLY ROM candidate;
- Stage1467 runtime regression after Mona12;
- full current dialogue Japanese-vs-Korean semantic audit.

NO_NEW_REAL.
