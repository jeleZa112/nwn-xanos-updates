# BGXAI 064 — Windows Syntax PASS, guarded updater 72–76 pinned, install NOT authorized

Дата: 2026-11-12.

## Real evidence from user
- The Windows PowerShell one-line `Parser.ParseInput` of immutable source-only draft `BGXAI_SYNC_072_076_DRAFT.ps1` returned **`BGXAI 064 SYNTAX PASS`**. This confirms Windows PowerShell syntax but NOT a test of menu 73/74/WeiDU.
- Prior user's own live EET: `BGX64 AREACHECK true true`, real EEex equality reading two party sprites' `m_pArea`. Not an in-weapon-hit safety proof.
- Prior live Windows updater: 068 last WeiDU 061 True, BCS and Lua staged/live matches; 071 `064_SOURCE_ONLY_PREFLIGHT_PASS` source SHA verification. Do NOT request repeats.

## Source-only guarded installer validation
- Additional post-rollback status bug found: after a successful 064→061 WeiDU rollback, the BGX64 staging folder legitimately persists, so a read-only status must **not** reject otherwise valid 061 solely for a stage-collision. Fixed the *status path* only: `main(status)` for WeiDU-last=061 runs `read_only.check(game_root)`; guarded new installation `read_status_061` still blocks if BGX64 folder exists.
- Confirmed **47/47 source/mock tests passed** under Python 3.11/Linux, including WeiDU install/rollback simulation, late game-process guard, wrong-game-path denial, sha pins, and status after rollback. No real Windows WeiDU install/uninstall was run.
- Updated GitHub source-only `BGXAI/fox_new/experimental_064_guarded_weidu_source_only/BGXAI64_INSTALL_SOURCE_ONLY.py`, `test_064_install_mock.py`, `manifest.json`. Manifest describes exactly 10 files; local package 10/10 size/SHA256 valid. Library directory `/BALDURS_GATE_EET_AI/BUILD/BGXAI_064_GUARDED_WEIDU_SOURCE_ONLY/` contains the two fixed source files and updated manifest.
- Important: the earlier ZIP archive was built *before* the last status test fix. Do not publish or use this older ZIP as the install source: **the live updater always downloads from SHA-pinned GitHub manifest instead.**

## Confirmed pinned one-file updater
- Original unchanged user CMD `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` fetches `BGXAI/fox_new/BOOTSTRAP_PIN.json` channel `bg-eet-ai`.
- Current channel pin references immutable commit **`d66ae072c4a1466521d384c15fe5c0c1ed6205cc`** and script `BGXAI/BGXAI_SYNC.ps1`: Git blob `ffb7558caf39e8f640dc02386c37c536b4bf6fbf`, SHA256 **`d246e6e286f760a1824c65e73e42ff2d8d29f5aa0fb46c1fb97409e04f06c1b1`**, size **59433**. Same commit also contains updated SHA pinned guarded package manifest and fixed installer+test. README/manifest and 10-file contract present.
- Old menu **1–71 preserved**, new:
  - **72** download/verify guarded 064 source only
  - **73** guarded 064 source-sync + real-game **read-only preflight**, no WeiDU/game writes
  - **74** EXPERIMENTAL install Lua-only BGX64 via WeiDU **only after explicit typed `INSTALL_BGXAI_064`**, and multiple SHA/backup/closed-game gates
  - **75** installed 061/064 read-only status
  - **76** explicit typed `ROLLBACK_BGXAI_064` + guarded backup and WeiDU rollback
- Pinned GitHub script fetch does not mean any action executed in user's actual game. No one has shown real menu 73 run. BGXAI 061 remains installed; BGXAI 064 NOT installed. No blanket installation consent.

## Next user action
User launches the **same** existing `BGXAI_UPDATE.cmd`, selects **73** ONCE and sends output. Option 73 syncs files under `BGXAI_DEV/experimental_064_guarded` and runs read-only preflight. Do not separately select 72, and **do NOT select 74** yet. If no new options or STOP, inspect output before retry. Keep installed game unchanged until genuine installed-game preflight passes and explicit user approval to install.
