# BG_EET_RU — V107 Windows source-fingerprint PASS and guarded V108 release

Date: 2026-11-23. Source: user's local ZIP, inspected offline; user ZIP and raw console are **not published**.

## Windows verified V107
- Actual ZIP: 124 unique entries, CRC PASS; `53_V107_CITEM_STATIC_ABI_PREFLIGHT.json` gives status `V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD`, `game_files_written=0`.
- V106 installed module SHA `4130359dc7778e816ad2bbf1cca20152e48fa9df4907d6411a793c0754e09bc6`; previously proven 2 console event lines (registration/transport only; not names, hits or misses).
- `EEex_Sprite.lua` SHA `4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28` and `EEex_Sprite_Patch.lua` SHA `e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f`, **both match** their V104 recorded SHA values.
- V107's `matches_v104...` FALSE for the patch is a **false negative**: the expected literal contained only 63 hex digits (omitted final `f`). Onefile source V108 and staging V107 source corrected to full 64-character SHA, with length assertion. This was **not** corruption of installed EEex.

## V108 safe default, optional experimental callback
- Manifest `bg-eet-ru/onefile/release.json`: version **108**, `game_writes_allowed=false` for normal updater execution; exact updater SHA256 `a1bc5c1641dfcc2e6fe80fc66ec51752db9fc3d28f73a75f5b46938d0f4b0244`. Source commit `f9c094528b6d3248523178db6911663ef93e54a9`; manifest commit `c3c5bd6b0e9b0603e5fc11a8c2ac3c6257465a4a`.
- Guarded native CItem probe with `weapon.cResRef:get()` and `launcher.cResRef:get()` is **NOT installed**. Exactly one existing observer Lua may be replaced only after strict Windows SHA checks, closed game, SHA-verified external backup and typed approval `INSTALL_BG_EET_RU_V108_NATIVE_ITEM_READ` via the original updater's `--install-v108-native-read` option. Exact rollback: `--rollback-v108-native-read` and `ROLLBACK_BG_EET_RU_V108_NATIVE_ITEM_READ`.
- No new listener, cap 8 native events, no damage/AI/UI changes. `ammo`, misses, journal correlation still **UNVERIFIED**. Runtime native pointer safety cannot be proven by CI; `pcall` does not catch native crashes. Game testing must be done only with informed user's consent.
- Existing updater also supports `--capture-v108-native-read` and appends a new structured entry `54_V108_NATIVE_ITEM_RESREF_PILOT.json` into existing single ZIP.
- CI PASS: full onefile `45143800110`; existing V106 regression + release pin `45143942985`; exact Windows V106 module-source reconstruction and synthetic native Lua callback `45144219822`; full V108 synthetic install, rollback, PREPARED recovery and tamper safe-stop `45144378632`.

**Status:** Windows V107 STATIC PASS; V108 RELEASE and offline CI PASS; V108 Windows deployment **NOT DONE**; live weapon RESREF **NOT PROVEN**. Do not rerun old V106 capture or modify V101 FULL/BRIEF, BGXAI, Voice, saves, TLK, EEex_Main, EXE.
