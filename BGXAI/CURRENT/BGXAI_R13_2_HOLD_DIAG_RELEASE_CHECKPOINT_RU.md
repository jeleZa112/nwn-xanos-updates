# BGXAI R13.2 — HOLD diagnostic guarded release (23 Nov 2026)

## Evidence and correction
User's REAL combat console `BGXAI_R13_CONSOLE_20261123T061617028509Z.log` confirmed R13 SESSION/READY and 3 DEFENSE events (partyIndex 2,1,2), all HOLD. Party actor 139200587 was recorded with selectedWeaponRaw=10, and actor 139266124 with selectedWeaponRaw=12, attack action ID 3. Raw target defensive fields were all null, but previous runtime did not serialize reason or context on HOLD. The test is VALID. Do not ask for repeat of old fight.

Official IESDP: 10 = SLOT_FIST, 12 = SLOT_AMMO1, 35–38 = SLOT_WEAPON(0–3). Original code mistakenly rejected slot10 and compared Lua EEex userdata with rawequal across getters; these checks can reject stable numeric IDs. R13.2:
- passively classifies selected slots FIST, AMMO, WEAPON; FIST does not dereference a CItem.
- records q.reason from HOLD safely and actor/target/action/slot from raw original started-action context, even if core gives HOLD.
- revalidates numeric target ID, sprite type, source action, selected slot/ability before and after double read. It no longer treats Lua-wrapper rawequal as native identity proof.
- retains all nine raw target defensive fields incl m_nResistMissile and bounded 64 events; no item/APR/hostility hit chance or combat queue proof, no authorization for weapon switch.
- adds error telemetry HOLD_RUNTIME if callback throws.
- retains old [BGXTD13] log prefix for console continuity; source files staged as R15_M_BGXD13.lua, installed as same 8-char resource M_BGXD13.lua.

## Release / proof
- CODE developed, SOURCE_ONLY and isolated TEST PASS. **DEPLOY TD15=NOT INSTALLED, LIVE TD15=NOT VERIFIED**.
- Windows CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45125194435 success: 20/20 Python guarded installer tests, Lua 5.4 runtime smoke PASS, Windows PowerShell 5.1 and 7 AST PASS, menu 1..163 present. Existing actions 1..162 preserved by exact source roundtrip regression before release.
- Immutable GitHub release: `575de4837a8adfdb4db8bc7a8d6503619829c4b7`.
- PIN promotion: `476efec9855f81f41f0bbc6b77ac14579de17fc7`.
- BGXAI_SYNC.ps1 SHA256 `f5b9d565de595ffea0e04c26f3194152445a26743aa47348694b883cdd9ec8e0`, 79631 bytes; main existing CMD unchanged.
- Guarded Python SHA256 `3c9f6b1837f92d6088b2fccf679b5985af96ddbc8509ade75e913436d75f90d0`, 15623 bytes.
- New passive Lua SHA256 `040a5df62c84363fd0d566c9509636efba7721439afcc90c72758da094e7f5f8`, 14030 bytes.
- Previous TD14 Lua SHA256 `c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511`; previous BGXTDEF13 Lua SHA256 `5c77a460d6b429cec6f9f81e7bf6883ee1f59474cfb95778091ab769302ef414`.
- Library source code, manifest and tests under /BALDURS_GATE_EET_AI/BUILD/R13_2_HOLD_DIAG_SOURCE_ONLY, ZIP /BALDURS_GATE_EET_AI/BUILD/BGXAI_R13_2_HOLD_DIAGNOSTICS_SOURCE_ONLY.zip.

## Next (one user action with typed approval; don't ask for separate preflight)
User closes game and InfinityLoader, runs `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, picks **163 → 3 Install**, types exact `INSTALL_BGXAI_R13_HOLD_DIAGNOSTIC` only if approving the guarded WeiDU overlay. Install itself performs read-only preflight and checks TD14-last/source hashes, verified external backup, WeiDU last-only and postinstall proof. Expected `BGXTD15_INSTALLED_AWAITING_LIVE_TEST`; if BGXTD15_STOP or another result, diagnose, don't repeat blindly or edit manually. The previous R13 / TD14 remain recoverable; only override/M_BGXD13.lua changes through WeiDU. No user-side extra CMD/ZIP.

After install, **163 → 5** is new readonly InfinityLoader console capture (old 162→5 requires TD14-last, so do not use that after TD15). If user is ready, do one minimal test with weapon or bare fists and actual enemy in existing test save and collect BGXAI_R13_2_CONSOLE_<timestamp>.log; do not require 8 attacks or long dangerous combat. Read reason and raw fields. Do NOT claim the target-defense read succeeded before live evidence.

Protect EPS, SCS, original R1–R4, BG_EET_RU, BG Voice RU, all saves and user-owned data. Never enable automatic weapon switching from passive candidate fields.