# BGXAI 079 — PRIEST MEMORY READONLY EVIDENCE — 2026-11-14

BGXAI 077 audit -> 078 automatic verified-healer fallback model -> 079 research/read-only EEex priest memorization probe all developed during current user request under rule automatic safe continue.

**Installed:** 066S verified live SHA `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`, EPS and F preserved. 067 HOLD, 068–079 source-only; no game files or auto-updater changed, no installations or new battle tests. BG Voice RU unrelated.

**079:** EEex modder Bubb example for sprite.m_memorizedSpellsPriest/getReference/EEex_Utility_IterateCPtrList/EEex_CastUD/EEex_IsBitUnset source https://forums.beamdog.com/discussion/71798/mod-eeex-v0-10-2-alpha/p44. Synthetic-read-only module `BGXAI079_PRIEST_MEMORY_READONLY.lua` receives injected API reader, counts matching memory entries & unused slot flags and returns **castable_now_verified=false, usable_now=nil** regardless of count. Error and unknown fail closed. 078 integration explicitly refuses to cast when only 079 memory evidence supplied. 27/27 Lua and 7/7 Python model tests PASS; original 078 included byte-identical for integration testing.

**Crucial limitation:** EEex 1.1.7 installed on user's real Windows game has NOT been used to run 079; BCS spell availability, dual unlock, silence/cast, line of sight, BCS range, real queue action all remain unverified. Program is not a live AI; do not install or activate, and do not say healing fixed. No request to replay old tests.

**Files:** Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_079_PRIEST_MEMORY_READONLY_SOURCE_ONLY/`, checkpoint `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_079_CHECKPOINT_20261114_RU.md`; GitHub branch `bg-eet-ai` same content in `BGXAI/fox_new/experimental_079_priest_memory_readonly_source_only/` and `BGXAI/CURRENT/BGXAI_079_CHECKPOINT_20261114_RU.md`.
