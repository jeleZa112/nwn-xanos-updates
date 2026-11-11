# BGXAI 062D — read-only EEex snapshot source prototype

Date 2026-11-12. **SOURCE ONLY, NOT INSTALLED.** Existing BGXAI 061 is installed and showed one successful in-game rescue (approach, buff, kill). No changes to the game or unified updater.

## Artifacts
Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_062D_READONLY_SNAPSHOT/` contains the actual source ZIP and README.
ZIP SHA256: `f6f1fda278b4fe18b66a5047a9079df63f8557129899ad72a25db30666278209`.

Created `BGX62_READONLY_SNAPSHOT.lua`: source-only function returning bounded portrait observations, reading only historically observed APIs (sprite portrait ID, object lookup, F=ON LOCALS, modal state, position), with safe pcall and no game commands. It is not attached to any listener or executed in EEex. It marks class, equipment, role, action queue, manual intent, stealth, consciousness and area **UNKNOWN**. No object pointer is exported and there is no inferred intercept authorization.

Created Python `snapshot_contract.py`: validates envelope, slot and object-ID uniqueness, strictly fails closed on unverified capabilities and refuses Python bool as F=1. Reuses prior 062B and 062C modules and tests. **54/54 synthetic unittest PASS** (29 prior +17 contract +8 static Lua safety). No native EEex runtime proof or Lua syntax test was done; these are simulation/static checks.

## Lesson
A role-capability system must distinguish unknown data from verified negative and verified positive. Never install an experimental module which guesses class/equipment or interrupts manual commands; existing BGX52Bridge remains sole guardian selector. Continue safe code work without asking for routine +; request explicit consent only for consequential live game installation.

## NEXT
Verify actual EEex 1.2.0 read-only APIs for class/kit, equipped weapon, current action and stealth against authoritative sources and a safe native probe when possible. Do not mark any field verified solely from historical names. Then integrate opt-in source-only capability gating and test the exact 061 BCS/Lua bridge; only publish updater preflight after source and SHA verification.
