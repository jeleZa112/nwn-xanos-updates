# BG_EET_RU — V107 READ ONLY release checkpoint
Date: 2026-11-23. No installation / no direct game modification.

## Verified release state
- Canonical updater: `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd`, `SELF_VERSION = 107`.
- Current manifest: `bg-eet-ru/onefile/release.json` with `version=107`, `game_writes_allowed=false`.
- SHA256 of exact updater source: `91af045538d068364f4f8057209acb64f12a7a67efd1133a9bf6a9397b971ec6` (manifest pin).
- Onefile update commit: `59a902fc385ffeb6c08de538583438d75fcc2086`; release manifest commit: `57e7f4a519a8a032078212543f6afea788798f02`.
- All integrated onefile tests: GitHub Actions run `45139481631` PASS; V106 regression plus release manifest SHA verification: run `45139882085` PASS. Earlier transient V106 CI failure on mismatched old version pin occurred before manifest update and was resolved.
- Source-only static preflight: `bg-eet-ru/weapon-identity/V107_STATIC_ABI_PREFLIGHT_SOURCE_ONLY.py`, source commit `caa433f56acf2b5a362c9c59adc941a6e76fbffc`. Offline isolated selftest passed.

## What V107 does
- During a normal run of the one canonical Windows updater (after V106 status), fingerprints relevant installed EEex Lua, DLL and loader files with bounded SHA256 reads.
- Records status in `53_V107_CITEM_STATIC_ABI_PREFLIGHT.json` inside the one existing external `SEND_TO_CHATGPT_BG_EET_RU.zip`, preserving existing reports.
- Does not execute native CItem methods, register listeners, modify the game, damage rolls, UI.MENU, BGXAI, voice, TLK, EXE, or saves.
- `runtime_native_resref_proven=false`, `ammunition_resref_verified=false`, `misses_verified=false`, `combat_journal_correlation_verified=false` until separate real runtime evidence.
- Previously installed V106 still has LIVE PASS **only** for recording damage callback events; no weapon/ammo proof.

## Remaining gate
1. User has not yet run the published V107 Windows read-only preflight; never claim Windows PASS or automatic game installation.
2. On Windows, launch only the usual updater without extra CMD/PowerShell; retrieve the same canonical ZIP and inspect `53_V107_CITEM_STATIC_ABI_PREFLIGHT.json`.
3. Assess ABI/version fingerprints and CItem callback lifetime. If inconclusive, remain HOLD; `pcall` does not prevent native crashes.
4. Future native V107 observer requires separate explicit typed authorization, external SHA-pinned backup, guarded one-CMD upgrade/rollback. Hit/miss and ammo still need independent proof.
5. Do not repeat V92–V106 completed tests, nor publish private user logs to GitHub.
