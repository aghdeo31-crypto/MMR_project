# MMR release-candidate gate v2 — system/UI first, name-entry critical

Date: 2026-09-19 KST

This project has already had two unsuccessful distribution attempts. The third attempt treats system/UI correctness as a higher release blocker than dialogue/font polish.

A build is NOT RC/release-ready merely because it boots or shows Korean.

## Priority order

1. NAME ENTRY / SYSTEM STATE SAFETY
2. SYSTEM / UI REGRESSION
3. FONT MAPPING / GLYPH IDENTITY
4. FONT ART QUALITY
5. JAPANESE-ORIGINAL TRANSLATION QA
6. FULL RUNTIME / RELEASE SWEEP

Dialogue/font-art work must never be allowed to hide or postpone a system/UI defect.

## Gate 0 — exact parent identity

PASS requires:
- exact intended parent ROM SHA256
- exact Stage/handoff lineage
- no stale Stage branch
- no untracked binary drift

Any mismatch: STOP.

## Gate 1 — NAME ENTRY CRITICAL

This is a hard release blocker.

PASS requires the SAME candidate SHA to pass all of the following:
- enter name setting from a normal new-game route
- initial/default state renders correctly
- every name-entry page opens
- page switch forward/backward repeatedly without freeze or state corruption
- cursor can reach every boundary cell
- no cursor/character-table overrun at left/right/top/bottom edges
- every visible selectable glyph resolves to the intended character
- confirm a normal name
- cancel/back from edit state
- delete/backspace path
- fill to maximum allowed length
- attempt one-more-character at max length without buffer corruption
- confirm after page switching
- save/commit the name
- leave name-entry UI and continue game
- reopen/return where applicable without stale KMODE/page state
- save -> reset -> load preserves the committed name
- no corruption in adjacent UI/system text after name entry
- no corruption of record-selection / Memory Center / new-game state
- runtime watch shows no out-of-range page/source-bank/index condition

Any freeze, wrong glyph, stale page, wrong saved name, buffer overwrite, or state leak = FAIL.

No release promotion is allowed with a NAME ENTRY workaround or "avoid this path" instruction.

## Gate 2 — SYSTEM / UI regression

PASS requires, on the same candidate SHA:
- boot/title
- Memory Center notice
- record selection
- new game
- system prompts
- menu open/close
- item/equipment/status UI
- shop/service UI
- battle UI/text
- save UI
- load UI
- small-font UI surfaces
- transitions between UI families
- repeated enter/exit cycles, not only first entry

Check:
- freeze/crash
- broken panel/tile
- stale KMODE/font mode
- wrong font family
- wrong character
- cursor misalignment
- palette/color corruption
- wrap/overflow
- state leakage into the next screen

## Gate 3 — glyph identity

PASS requires:
- all KS2350 IDs round-trip char -> 08 hi lo -> ID -> same char
- 2350 unique tokens
- translation/UI corpus contains no unsupported Hangul unless explicit extension exists
- critical sentinels 한/힌/이/히 exact
- name-entry selectable table token -> ID -> glyph identity exact
- encoded text token stream round-trip equals intended Korean before ROM insertion

This gate catches cases such as intended 한 resolving to 힌/이 because of mapping/token/slot errors.

## Gate 4 — font structural quality

PASS requires:
- blank glyph 0
- clipped glyph 0
- duplicate bitmap group 0
- pointer-bank boundary PASS
- font-only binary diff limited to approved font ranges

## Gate 5 — font art quality

Mona12 is a BASE, not final art.

Every low-distance pair used by the actual game/UI/name-entry corpus must enter the review queue.

Priority:
- P0: used in system/UI/name entry
- P1: both glyphs used in dialogue
- P2: one glyph used
- P3: unused

P0 must be reviewed first.

Known art-review targets:
- 개 / 게
- 애 / 에
- 독 / 득
- 눅 / 늑
- horizontal-vowel families ㅗ/ㅜ/ㅛ/ㅠ vs ㅡ
- initial/final ㄹ/ㅌ and ㄷ/ㅁ families when flagged by actual usage

한/힌 and 한/이 are NOT art-similarity suspects; audit mapping/token/runtime state first.

## Gate 6 — small-font family

No release while menu/status/name-entry small fonts remain an inconsistent engineering mix.

Rules:
- never geometrically shrink the 12x12 dialogue font
- make size-specific pixel designs
- name-entry font/table receives its own QA
- retain original numbers/Latin where they visually fit better
- audit ambiguous Korean pairs separately for each size
- capture every UI family before promotion

## Gate 7 — Japanese-original translation authority

PASS requires:
- dialogue edits based on exact Japanese original
- English text auxiliary only
- no English offset/order used as Japanese record authority
- control-token sequence unchanged
- unresolved JP binding remains HOLD, never guessed

## Gate 8 — static binary regression

PASS requires:
- only intended regions changed
- protected source 0x58 unchanged
- D12/KMODE/ECC6 changes only in a Stage explicitly targeting them
- pointer table unchanged unless explicitly targeted
- forward readback exact
- reverse restoration exact
- checksum/complement expected

## Gate 9 — full runtime matrix

A release candidate must pass the SAME build on all required paths.

Evidence from another build name/SHA is invalid.

## Gate 10 — language/art sweep

Before release:
- Japanese remnants
- broken/garbled glyphs
- wrong-character sweep
- system/UI wording
- Japanese-original semantic pass
- terminology
- awkward Korean
- wrap/overflow
- punctuation/spacing
- all name-entry visible glyphs

## Promotion rule

RELEASE_ALLOWED = true only when every gate above is PASS on one exact candidate SHA.

Especially:
- NAME ENTRY CRITICAL must be PASS
- SYSTEM/UI regression must be PASS
- no release with a known "minor" system/UI defect

Until then classification must be:
- DEV
- STATIC_CANDIDATE
- RUNTIME_TEST
- HOLD

Never label an untested build RC/final.
