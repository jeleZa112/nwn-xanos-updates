# BG_EET_RU — V107 Windows fingerprint audit; V104/V107 false mismatch finding
Date 2026-11-23. Evidence is user's privately submitted `SEND_TO_CHATGPT_BG_EET_RU(20261123-085523).zip`; **do not upload the ZIP**.

## Authenticated user-side result
- ZIP SHA256 `f216909e0cc679436cf512fc722672375f05e01b5370c1076f7ca9d03cb94dcb`, **124 entries**, CRC PASS, no duplicates.
- `53_V107_CITEM_STATIC_ABI_PREFLIGHT.json`: `V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD`, updater_version 107, `game_files_written=0`, `v106_installed_state_present=true`.
- Installed V106 module SHA256 `4130359dc7778e816ad2bbf1cca20152e48fa9df4907d6411a793c0754e09bc6` is equal to V106 state's `installed_module_sha256`; no reinstall required.
- Historic V106 console evidence: 1 SOURCE_LOADED, 1 START, 2 events; native RESREF/hit/miss/ammo/log correlation NOT established.
- `EEex.dll` fingerprint SHA256 `b6c7c98804360cb46531db75ab9608e378fd403d60c29c0e29946a60a334276a`, `Baldur.exe` SHA256 `fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580`. These fingerprints identify the current files; do not infer an upstream binary distribution/version match from hash alone.

## Independent V104 vs V107 comparison (of archived evidence)
|File|V104 SHA256|V107 SHA256|Independent match|V107 diagnostic flag|
|---|---|---|---|---|
|EEex_scripts/EEex_Sprite.lua|`4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28`|same|true|true|
|EEex_scripts/EEex_Sprite_Patch.lua|`e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f`|same|true|**false**|

Both sizes also equal across archived snapshots. Therefore the V107 embedded aggregate `v104_sprite_source_sha_match=false` is an **incorrect flag**, not evidence that the file changed; the two stored digests and sizes match. The underlying reason for the false-negative flag is not proven; user-side updater's exact binary code has not been recovered independently from the ZIP. Don't invent a root cause. Do not ask user to rerun V107 solely to inspect this flag.

## EEex callback source evidence
Gibberlings3 Tweaks Anthology `cdtweaks/luke/lua/class/overwhelming_devastating_critical.lua` uses `EEex_Sprite_AddAlterBaseWeaponDamageListener(function(context)` and `context.weapon.cResRef:get()` **inside that same type of callback**, with `context.launcher` separated. This materially improves source API evidence, but NOT user-side lifetime/ABI proof. `pcall` cannot catch native memory errors; must remain guarded.

## Next safe step
- Build/inspect source-only exact bounded callback probe with native reading disabled by default; verify no duplicate listener registration and no game writes. Only deploy through existing updater after SHA, external backup, verified source/installed build, typed user consent and rollback.
- Future live step: separate `weapon` vs `launcher` vs actual ammo; don't claim damage callback handles misses; tie log row only after independent evidence.
- Do not touch BGXAI, Voice, UI, saves, TLK; do not repeat V92-V107 prior tests.
