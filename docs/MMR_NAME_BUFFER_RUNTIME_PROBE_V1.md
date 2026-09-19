# MMR name-buffer runtime probe v1

Date: 2026-09-19 KST
Classification: EXTERNAL-CLUE-GUIDED READ-ONLY PROBE / NOT AUTHORITY

## Why

Two MMR cheat/code references independently identify:
- Hunter name bytes around 7E:8000
- additional characters at +0x100 for later human party members
- Tank #1 name around 7E:8300

One source describes hunter positions 1..5 as 7E:8000..8004 and notes that the fifth character can extend outside the visible frame.
Another source describes hunter name 1..4 at 7E:8000 and tank #1 name 1..6 at 7E:8300.

These are useful clues, but not project authority.

## Probe

tools/mmr_name_buffer_probe.lua

It watches WRAM writes only:
- 7E:8000..8004
- 7E:8300..8305

It logs:
- address
- byte value
- PC
- A/X/Y when emulator state exposes them

No write is performed by the script.

## Required original-JP confirmation

During Japanese original name entry:
1. start with initial/default name;
2. delete characters one by one;
3. enter exactly 1,2,3,4,5 characters for hunter where possible;
4. complete/confirm;
5. repeat a tank name-entry screen and test 1..6 where possible;
6. compare writes and post-confirm values.

Promote an address only if original-JP runtime writes/readback match the visible name semantics.

## Why this matters for the third release

This can close:
- actual hunter max length
- actual tank max length
- visible frame vs storage length
- one-byte vs extended Korean storage behavior
- final committed buffer vs temporary editor buffer

Do NOT redesign name limits from the Korean UI before this original-JP probe is checked.
