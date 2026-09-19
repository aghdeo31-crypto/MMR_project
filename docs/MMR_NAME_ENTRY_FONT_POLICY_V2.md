# MMR 이름설정/소형 UI 폰트 정책 v2

Date: 2026-09-19 KST
Status: supersedes the old assumption that name entry should share the dialogue 12x12 font.

## 핵심 변경

사용자 런타임 관찰:
- 이름설정 글자 크기가 대사 글자보다 작다.
- 이름설정 커서가 위/아래 글자에 걸쳐 움직이는 문제가 있다.

따라서 이름설정은 대사 폰트와 같은 12x12 글리프를 쓰는 화면으로 취급하지 않는다.

## 폰트 패밀리 분리

### Dialogue / large text
- base: Mona12 Regular
- native px: 12
- active raster: 12x12
- MMR Custom art layer 사용

### Name entry / compact UI
- base candidate: Mona10 Regular
- native px: 10
- raster candidate: 10x12
- actual visible body on current 200-char set: mostly 8~9 px wide x 8~9 px high
- no geometric scaling
- MMR small-font-specific art layer 사용
- name-entry cursor/cell geometry is NOT derived from 10x12; measure Japanese original

### Other small UI
Do not automatically reuse the name font.
Classify each UI surface by original Japanese glyph size/cell pitch first.
Candidate families may include Mona10/native smaller pixel art, but each renderer/table needs its own contract.

## Why the old 12x12 name-entry handoff is superseded

The old handoff correctly stated that actual cell step, row spacing and cursor rectangle still required original-JP measurement, but it labelled the name-entry glyph baseline as 12x12.

Runtime observation now shows the name-entry font is visibly smaller than dialogue.
Therefore:
- old 12x12 name glyph size = superseded assumption
- logical 4 pages x 50 / 10x5 = retained as a logical layout candidate
- physical font/cell/cursor geometry = reopened and original-driven

## Mona10 Custom v0.1

User-provided Mona package contains native Mona10 Regular/Bold.

First candidate:
- Mona10 Regular 10px
- 10x12 neutral raster
- y=0
- horizontally centered
- 200 logical name-entry chars
- 0 blank
- 0 clip
- 0 duplicate bitmap

Small-raster art correction:
- for ㅡ medial syllables, shorten a dominant >=8px bar by 1px each side
- changed initial 200-char set: 은, 근, 승, 플, 흑, 늑

This removes the only <=1-pixel pair in the current 200-char candidate.
Low-distance pairs still require manual/runtime review.

## Cursor rule

Never resize/move the font merely to hide cursor overlap.

Measure from Japanese original:
- visible glyph bbox
- row-to-row baseline/anchor
- cursor Y origin
- cursor rectangle/highlight height
- cursor row step
- adjacent-row overlap

Then design the Korean physical grid around that contract.

Required:
- adjacent visible-row overlap = 0 px
- cursor aligns with exactly one selected row
- all 5 rows stable
- page switching preserves a valid cursor state

## Release rule

NAME_ENTRY_CRITICAL remains FAIL until:
1. JP original geometry measured;
2. Mona10-or-other small-font candidate bound to verified physical slots;
3. cursor geometry corrected independently of font;
4. 200 visible glyph -> selected glyph identity passes;
5. max-length/save/reset/load passes;
6. all four pages pass on one exact candidate SHA.

No RC/final while name-entry uses the dialogue font by assumption.
