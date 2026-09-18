# MMR Stage1468 — Mona12 FONT_ASSETS_ONLY static preparation

Date: 2026-09-19 KST
Status: OFFLINE_PREP / NO_NEW_REAL

## Exact parent authority

Current parent remains Stage1467 RC2_TEST.

- ROM: Metal_Max_Returns_Korean_RC2_TEST_20260918.sfc
- exact local path previously reported:
  H:\한글화\MMR_Project\referenced-chatgpt-conversation-this-is-an-2\work\release\stage1467\Metal_Max_Returns_Korean_RC2_TEST_20260918.sfc
- SHA256:
  29EBF0A5DAB0A646FF9AF6E68127AAE6C8182AB2129C2819FB37177A94453BEB
- record-select freeze fix / Memory Center notice fix remain parent behavior.
- name input 4 pages + save, target5, 38/38 regression and status16/field6 lifetime were previously reported PASS.
- Stage1459 RC1 stays superseded/HOLD.

## New font-side closure

Recovered Stage432 native12 authority:
- KS X 1001 2350 glyphs
- 25-byte record = width 0x0C + 12 LE16 column words
- pointer table EA:C000, 2400 x LE24
- EB:8000 1310 records
- EC:8000 1040 records
- EC:E600 blank fail-safe for IDs 2350..2399

Mona12 Regular primary:
- 12 px / 12x12 / y=-1 / horizontally centered
- KS2350 slot ordering matches Stage432 private-token pilot 4/4:
  탄 ID1999 = 08 0D AF
  약 ID1379 = 08 09 C3
  보 ID963  = 08 07 63
  급 ID155  = 08 01 FB

New orientation resolver:
- bit0_top bank synthetic test -> PASS_BIT0_TOP
- bit15_top bank synthetic test -> PASS_BIT15_TOP
- pointer-table 1-byte corruption -> HOLD_POINTER_LAYOUT_MISMATCH
- it selects orientation from the 4 unused padding bits across all 2350 records, not from visual guessing.

New FONT_ASSETS_ONLY builder:
- requires exact Stage1467 SHA above
- validates current 2400-entry pointer table and blank fail-safe
- resolves current orientation automatically
- replaces ONLY:
  - file 0x358000..0x35FFEE (EB 1310)
  - file 0x360000..0x366590 (EC 1040)
- does NOT modify:
  pointer table, blank fail-safe, D12 redirect, KMODE, ECC6, source token 0x58, translation bytes, or checksum bytes.
- synthetic test: exactly three intentional font-byte mutations corrected; changed_bytes=3; all non-font surfaces unchanged.

One-click static runner:
  scripts/RUN_STAGE1468_MONA12_FONT_ASSETS_ONLY.ps1

It pins Stage1467 SHA, runs orientation resolution, builds the font-only child, then runs the existing FONT_ONLY diff gate.

## Translation policy unchanged

Japanese original is top authority.
English is auxiliary reference only.
No ordinal/English-ROM offset binding.
No dialogue EDIT without exact-JP binding + readable Japanese source evidence.

## Current boundary

Codex/DevSpace is not exposed in this chat, so the exact local Stage1467 ROM has not been read or rewritten here.
No Stage1468 candidate ROM hash exists yet.
No runtime/Mesen promotion is claimed.

Exact next execution once local workspace access returns:
1. place/use Mona12.ttf locally without committing the font file;
2. run the Stage1468 PowerShell runner against the exact Stage1467 baseline;
3. require orientation PASS + FONT_ONLY diff PASS;
4. runtime smoke FONT_ASSETS_ONLY before any dialogue/renderer code change;
5. if normal, keep Mona12 bank and continue Japanese-original dialogue review.

NO_NEW_REAL.
