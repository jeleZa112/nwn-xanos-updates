# BGXAI 063 — Native Lua semantics checkpoint, 2026-11-12

## Actual work verified
Created native Lua 5.4 harness via `ctypes` + `liblua5.4.so.0`. **103/103 unittest PASS** in one combined run. 19 new native Lua tests run actual Lua code under mocked EEex:
- 11 tests of the **exact** BGXAI 062E read-only class/action probe, including missing API, malformed sprites, invalid class/action, duplicate portrait, cap 6 slots, no battle commands.
- 8 tests of the **historical** 059 eligibility helper from a previously saved source archive, including one nearest eligible guardian, slot ties, blocked different area, missing sight, error rejection, no battle commands.
- Previous 062B/C/D/E regressions also executed in the same suite.

**One packaging error was caught and fixed:** initially the 062D baseline Lua file was absent and one regression test failed to import. It was copied into the merged suite, reran **103/103 PASS**. No fabricated first-time success.

## Source and Library
GitHub `BGXAI/fox_new/experimental_063_native_lua_readonly/` contains new `lua_harness.py`, two native test modules, SHA manifest, README. Dependencies:
- `BGXAI/fox_new/experimental_062e_class_action_source_only/BGX62E_CLASS_ACTION_PROBE.lua`
- `BGXAI/fox_new/experimental_059_guard_visibility_source_only/BGX59_ELIGIBILITY.lua` (historic, uninstalled candidate).
Archive with all sources and regressions: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_063_NATIVE_LUA_READONLY/BGXAI_063_NATIVE_LUA_READONLY.zip`.
ZIP SHA256 `0dd5ae428a227132d450aa3fa4030ffd6f1ba861487396d8fd0f3268b228d4c7`.

## Strict limitations
- Installed game **BGXAI 061 unchanged**, one confirmed live user episode: guardian moved, buffed, killed.
- Neither Lua 5.4 mock nor historical 059 eligibility is proof that the user's installed EEex 1.2.0 or installed M_BX43.lua 061 behaves identically. Do not claim a native EEex test; do not install 063.
- BGXAI 063 is offline verification technology, not an autonomous AI feature yet. The existing BGX52Bridge remains the sole selector; no second arbiter.
- Current equipped-weapon and action ownership APIs are not proven in the user's installed runtime; class ID alone is not capability, current action ID alone does not prove absence of manual queues.
- Existing BGXAI_UPDATE.cmd remains only delivery and future opt-in path, no manual new installer.

## Next actionable boundary
Run native source-only validation against the **exact installed 061 Lua source** or runtime read-only diagnostic from existing updater (option 68 if needed). Then design role-aware eligibility integrated only into existing bridge while respecting manual/EPS actions. Avoid extending installed game until live capability evidence and explicit consent.
