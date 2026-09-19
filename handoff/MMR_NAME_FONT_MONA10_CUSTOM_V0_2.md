# MMR Name Font — Mona10 Custom v0.2

Date: 2026-09-19 KST
Status: STATIC SMALL-FONT CANDIDATE / ROM WRITE HOLD

## Supersedes v0.1

v0.1 used a broad ㅡ horizontal-run search. During deeper review, syllable layout variation showed that a generic row search could sometimes pick a consonant stroke instead of the medial vowel.

Therefore v0.1 is not promoted.

v0.2 is counterpart-aware:
- ㅓ is compared against the same L/T syllable with ㅣ.
- ㅡ is compared against the same L/T syllable with ㅗ.
- ㅕ is compared against the same L/T syllable with ㅓ.
- an art tweak is applied only when the base pair is actually <=2 pixels apart.

No geometric scaling.

## Result on 200 name-entry characters

Base:
- Mona10 Regular 10px
- raster candidate 10x12
- blank 0
- clip 0
- duplicate bitmap 0

v0.1:
- <=2 pixel confusable pairs: 17

v0.2:
- <=1: 0
- <=2: 2

Only remaining <=2 pairs:
- 로 / 토
- 트 / 르

These are not auto-modified because their visual difference is a left-vs-right vertical-stroke placement of ㄹ/ㅌ, which remains visually distinct despite low Hamming count. Forcing more pixels would distort the original forms more than it helps.

## Remaining mandatory blocker

Do NOT write this to the release ROM yet.

Japanese original name-entry must first provide:
- actual visible glyph bbox
- physical row pitch
- cursor Y step
- cursor rectangle/highlight height
- cursor anchor relative to selected glyph
- top/bottom row behavior

Candidate rule:
- name font stays smaller than dialogue font
- cursor adjacent-row overlap = 0 px
- cursor selects exactly one row
- font position is not shifted merely to hide a cursor bug

## Next local execution

When Codex/DevSpace returns:
1. enter Japanese original name-entry screen and capture rows 1..N;
2. measure original glyph occupancy/cursor geometry;
3. bind Mona10 v0.2 to the actual small-font renderer/table, not the dialogue font path;
4. correct cursor geometry independently;
5. test all 4 Korean pages and 200 visible-glyph -> selected-glyph identity;
6. save/reset/load;
7. only after PASS, integrate with system/UI regression candidate.

NO_NEW_REAL runtime evidence in this handoff.
