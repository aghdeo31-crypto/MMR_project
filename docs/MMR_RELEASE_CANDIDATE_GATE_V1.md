# MMR release-candidate gate v1 — third-attempt quality policy

Date: 2026-09-19 KST

This project has already had two unsuccessful distribution attempts. From this point, a build is NOT called RC/release-ready just because it boots or shows Korean.

## Gate 0 — exact parent identity
PASS requires:
- exact intended parent ROM SHA256
- exact Stage/handoff lineage
- no stale Stage branch
- no untracked binary drift

Any mismatch: STOP.

## Gate 1 — glyph identity
PASS requires:
- all KS2350 IDs round-trip char -> 08 hi lo -> ID -> same char
- 2350 unique tokens
- translation corpus contains no Hangul outside supported set unless an explicit extension exists
- critical sentinels 한/힌/이/히 all exact
- encoded dialogue token stream round-trip equals intended Korean before ROM insertion

This is the gate intended to catch cases such as intended '한' rendering as another Hangul due to mapping/token/slot error.

## Gate 2 — font structural quality
PASS requires:
- blank glyph 0
- clipped glyph 0
- duplicate bitmap group 0
- pointer-bank boundary PASS
- font-only binary diff limited to approved font ranges

## Gate 3 — font art quality
Mona12 is a BASE, not final art.

Every low-distance pair used by the actual game corpus must enter the review queue.
Priority:
- P0: both glyphs used in game
- P1: one glyph used
- P2: unused

P0 must be visually reviewed at 1x pixel, nearest-neighbor enlarged, and CRT-like runtime capture.
If ambiguous, create an explicit MMR override glyph. Do not rewrite the translation to avoid the glyph.

Known initial art-review targets:
- 개 / 게
- 애 / 에
- 독 / 득
- 눅 / 늑
- horizontal-vowel families ㅗ/ㅜ/ㅛ/ㅠ vs ㅡ
- initial/final ㄹ/ㅌ and ㄷ/ㅁ families when flagged by corpus usage

한/힌 and 한/이 are NOT currently art-similarity suspects; token/slot/runtime mapping must be audited first.

## Gate 4 — small-font family
No final release while menu/status/name-entry small fonts are still an inconsistent engineering mix.

Rules:
- never geometrically shrink the 12x12 dialogue font
- make size-specific pixel designs
- retain original numbers/Latin where they visually fit better
- audit ambiguous Korean pairs separately for each size
- screenshot each UI family before promotion

## Gate 5 — Japanese-original translation authority
PASS requires:
- dialogue edits based on exact Japanese original
- English text auxiliary only
- no English offset/order used as Japanese record authority
- control-token sequence unchanged
- unresolved JP binding remains HOLD, never guessed

## Gate 6 — static binary regression
PASS requires:
- only intended regions changed
- protected source 0x58 unchanged
- D12/KMODE/ECC6 unchanged during FONT_ASSETS_ONLY stage
- pointer table unchanged unless the stage explicitly targets it
- forward readback exact
- reverse restoration exact
- checksum/complement expected

## Gate 7 — runtime matrix
A release candidate must pass the SAME build on all required paths:
1. boot/title
2. Memory Center notice
3. record selection (no freeze)
4. new game path
5. name input all 4 pages + save
6. ordinary field dialogue
7. shop/service dialogue
8. item/equipment/status menus
9. battle text
10. save -> reset -> load
11. long session transition across multiple dialogue records
12. small-font/UI screens

A screenshot from another build name does not certify the candidate.

## Gate 8 — language/art sweep
Before release:
- Japanese remnants sweep
- broken/garbled glyph sweep
- wrong-character sweep
- Japanese-original semantic pass
- terminology pass
- awkward Korean pass
- wrap/overflow pass
- punctuation/spacing pass

## Promotion rule

RELEASE_ALLOWED = true only when Gates 0..8 are PASS on one exact candidate SHA.

Until then classification must be one of:
- DEV
- STATIC_CANDIDATE
- RUNTIME_TEST
- HOLD

Never label an untested build RC/final.
