# BGXAI 064: EEex native same-area equality live PASS (2026-11-12)

User screenshot from Baldur's Gate Enhanced Edition Trilogy v2.6.6.0 in their current EET shows the Lua console output:

```text
BGX64 AREACHECK true true
```

The executed read-only console expression loaded `EEex_GameObject_Get(EEex_Sprite_GetInPortraitID(0))` and index 1, and called `EEex_UDEqual(p.m_pArea,q.m_pArea)` inside `pcall` on two party members standing in the same area. The result means the native API is present, readable on those live objects, and returned boolean true with no Lua exception.

This is stronger than prior `AREAAPI=function` and mock tests. **It is not a test of behavior inside the weapon-hit callback, and cannot establish success for companions in two different areas**; the patch is a restrictive fail-closed filter and does not replace the working 061 until separately authorized.

Prior live Windows preflights:
- Menu 68: 061 WeiDU last True, live/staged BCS and Lua identical.
- Menu 71: pinned script `75e61c00754d`, 10/10 sources VERIFIED, `064_SOURCE_ONLY_PREFLIGHT_PASS`, `game_written=false`, `eeex_runtime_area_api=NOT_CHECKED` at the moment of 71; this console result closes **the same-area API smoke observation** (not an automated 71 field).
- Live 061 BCS SHA256 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`; Lua `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`.
- Source-only 064 Lua candidate SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.

Next: finish native-safe opt-in WeiDU installer/recovery release and source checks within the existing one-file updater; game installation remains a separate explicit authorization with verified external backup. No need to repeat 68, 71 or console area check, and no need to fight Shank.

Working game stays BGXAI 061 installed, 064 not installed. Global auto-continue rule: progress through safe steps without requiring user '+' within current active response; don't claim background work after answer.
