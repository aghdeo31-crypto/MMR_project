# MMR font art quality — Mona12 Custom v0.1

Date: 2026-09-19 KST
Classification: STATIC_CUSTOM_CANDIDATE / NO_NEW_REAL

## Why this exists

Mona12 Regular passes structural QA (2350 nonblank, no clipping, no duplicate bitmaps) but many one-jamo neighbor pairs are too close for a CRT-era 12x12 RPG font.

Important diagnosis:
- 한/힌 = 39 differing pixels
- 한/이 = 60
Therefore a runtime case where intended 한 becomes 힌/이 is not explained by Mona12 visual similarity. Audit token -> ID -> slot/runtime mapping first.

Actual art weaknesses include:
- 독/득 = 1 pixel
- 눅/늑 = 1
- 돌/들 = 1
- 굴/글 = 1
- 종/증 = 2
- 용/응 = 2
- 개/게 = 3
- 애/에 = 3

## v0.1 art rule

For Jungseong ㅡ syllables only:
- find the dominant horizontal vowel run in rows 2..7
- if length >=9, remove exactly one endpoint pixel on both sides
- no resizing
- no movement of other components

155 / 2350 KS glyphs change.

Effect:
- hamming <=1 one-jamo pairs: 166 -> 29
- <=2: 601 -> 317
- <=3: 1198 -> 1047
- blank: 0
- clipped: 0
- duplicate bitmap groups: 0

Representative improvement:
- 독/득 1 -> 3
- 눅/늑 1 -> 3
- 돌/들 1 -> 3
- 굴/글 1 -> 3
- 종/증 2 -> 4
- 용/응 2 -> 4

개/게 and 애/에 remain 3 and are next manual/component-art review targets.

## Promotion rule

Do not write this into a release ROM yet.
First:
1. run real translation corpus through visual-quality queue;
2. review all P0 pairs where both chars are actually used;
3. create explicit override layer for remaining ambiguous P0 pairs;
4. run KS2350 identity gate;
5. only then feed Custom v0.1+overrides to Stage1468 FONT_ASSETS_ONLY builder;
6. runtime matrix on one exact candidate SHA.

NO_NEW_REAL.
