# MMR Stage1468 continuation — Mona12 exact Stage432 KS2350 layout prep

Date: 2026-09-19 KST
Scope: OFFLINE_PREP_NO_ROM_WRITE
New REAL: NO_NEW_REAL

## Newly closed

Recovered Stage432 authority fixes the current Korean native12 bank contract:
- KS X 1001 = 2350 Hangul glyphs.
- record = width 0x0C + 12 little-endian 16-bit column words = 25 bytes.
- pointer table = 2400 entries at $EA:C000.
- IDs 0..1309 = $EB:8000 sequential 25-byte records.
- IDs 1310..2349 = $EC:8000 sequential 25-byte records.
- IDs 2350..2399 = blank fail-safe $EC:E600.

The Stage432 pilot token formula:
  id=(hi-1)*160+(lo-0x60)
matches standard KS X 1001 order exactly for all four known glyphs:
- 탄 ID1999 / C5BA / 08 0D AF
- 약 ID1379 / BEE0 / 08 09 C3
- 보 ID963 / BAB8 / 08 07 63
- 급 ID155 / B1DE / 08 01 FB

Therefore the Mona12 font can use exact existing KS2350 slot order without any English-ROM row offsets or translation ordinal assumptions.

## Mona12 Stage432-layout build

Input:
- Mona12.ttf SHA256 b305cc135d9fc543792f7591dc9008a82e8cf1c9e6a4ed2127745e2924d000c1
- 12px / 12x12 / y=-1 / horizontally centered

Mechanical result:
- 2350 / 2350 nonblank
- 2350 / 2350 unique
- EB part 32750 bytes
- EC part 26000 bytes
- real record bank crossing 0
- pointer-table candidate 7200 bytes
- known pilot token match 4/4

One detail remains fail-closed:
- recovered docs specify LE16 column words, but do not expose top-pixel bit position.
- tool emits both bit0_top and bit15_top.
- neither is promoted until byte-exact comparison with the current Stage1467/Stage432 packer or a known current native12 record.

Tool:
- tools/mmr_mona12_stage432_ks2350_builder.py
- commit 78a4ff092b3ae1a14b21bfd04ef2979ce23a05f4

## Restart when Codex/DevSpace returns

1. Open H:\한글화\MMR_Project writable.
2. Verify latest Stage1467 authority/hashes.
3. Read current native12 packer or one known current glyph record.
4. Select bit0_top vs bit15_top only by byte-exact comparison.
5. Regenerate Mona12 KS2350.
6. Replace font/pointer assets only; leave Stage1467 runtime fixes untouched.
7. Run FONT_ONLY diff gate.
8. Runtime regression: Memory Center notice, record selection no freeze, new game, name input 4 pages/save, target5, 38/38, status16/field6.
9. Continue Japanese-original-first dialogue audit; English auxiliary only.

NO_NEW_REAL.
