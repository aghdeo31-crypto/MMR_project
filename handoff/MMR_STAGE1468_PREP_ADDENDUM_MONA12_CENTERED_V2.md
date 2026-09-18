# MMR Stage1468 PREP addendum — Mona12 centered v2 becomes primary raster candidate

Date: 2026-09-19 KST
Scope: OFFLINE_PREP_NO_ROM_WRITE
New REAL: NO_NEW_REAL

## Why v2 supersedes raw v1 for the first candidate

Historical Japanese-base font work preferred:
- active cell: 12x12
- Korean visible body: about 10x12
- body centered in the 12x12 active cell

Mona12 Regular at 12 px naturally produces:
- 6,878 Hangul glyphs with a 10 px visible width
- 4,294 Hangul glyphs with an 11 px visible width

Raw x=0 placement gives:
- 6,878 glyphs margins 0/2
- 4,294 glyphs margins 0/1

Centered v2 gives:
- 6,878 glyphs margins 1/1
- 4,294 glyphs margins 0/1
- clipping 0 / 11,172
- y=-1 retained

Therefore the first Stage1467-derived FONT_ONLY candidate should use:
  tools/mmr_mona12_source_builder_v2.py --align center

Raw v1 remains an A/B diagnostic only.

## Centered neutral source
- full Hangul glyphs: 11,172
- bytes: 268,128
- SHA256: 65bec9405d5e16ebe6c5c75c5e4f314a8a7be4a22a9f7f961d4cf89321f92249
- NOT MMR ROM format; feed through existing Stage1467 packer only.

## Git commits
- centered builder v2: 1861253c7e7d6e935c425f377e16d013b55090c6
- centered QA: 990cd1fb47ebb01a30988ea378682e821b91b048
- font-only diff selftest: 92775b4341fcee82ba44e365d65ad30d440d668d

## Restart rule
When Codex/DevSpace is writable, do NOT start from v1 raw.
Use centered v2 as primary, raw v1 only if the runtime screenshot shows spacing/centering regression.
