# BGXAI 064 — установка + отдельный статус 75 PASS (2026-11-12)

## Достоверный реальный вывод пользователя из C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd

### Меню 74 (WeiDU установка)
- Пользователь сам выбрал 74 и ввёл `INSTALL_BGXAI_064`.
- `status: INSTALLED_064_EXPERIMENTAL`.
- `after.status: INSTALLED_064_VERIFIED`.
- `after.last_weidu: ~BGX64\\SETUP-BGX64.TP2~ #0 #0 // BGXAI 064 same area guard, Lua only`.
- BCS SHA256: `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b` (unchanged from 061).
- Lua SHA256: `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- Installer returned external backup path `C:\Users\Drevo\Documents\BGXAI64_SAFE_BACKUPS\PRE_INSTALL_20261112T145406880539Z`. This is installer-reported, not manually opened/inspected.
- Four changed Lua anchors, single existing selector, rest code untouched.

### Меню 75 (independent Windows read-only status, latest user turn)
- Pinned updater identified `d66ae072c4a1`, SHA256 OK.
- Ten 064G source files verified; source sync already current; no game changes.
- `mode: READ_ONLY`.
- `proof.status: INSTALLED_064_VERIFIED`.
- `proof.last_weidu: ~BGX64\\SETUP-BGX64.TP2~ #0 #0 // BGXAI 064 same area guard, Lua only`.
- BCS SHA256 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`.
- Lua SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- `BGXAI: update/status action completed.` Normal exit.

## Current state / future boundary
- The **actual installed** AI is now experimental **BGXAI 064** (not 061).
- **NO rerun of 68, 71, 73, 74 or 75**. All completed successfully.
- Prior native console `BGX64 AREACHECK true true` confirms EEex_UDEqual can compare same-area sprites *outside on-hit hook*, but it does NOT demonstrate on-hit callback behavior. The new restriction may be fail-closed if native timing differs; need one live guarded combat test of 064.
- Next single practical test: run EET, save, leave autoattack against enemies OFF, enable F guard on two companion defenders, position them and protected party member in same area, then allow a weak enemy to hit the protected member; observe guardian response (approach/protect, EPS attack/skills), ideally compare to known 061 successful response. Request user report **what happened** and, only if behavior fails, relevant log/screenshot. Do not deliberately place anyone in a different ARE until same-area case succeeds.
- If 064 freezes, protection fails, or unexpectedly disrupts combat: stop test, preserve any logs, inspect; guarded rollback to 061 exists as menu 76 but do not trigger automatically, do not blindly retry if WeiDU/source integrity failure.
- Global AUTO_CONTINUE policy: progress safe source-only steps without asking for '+', but no background execution after final.
