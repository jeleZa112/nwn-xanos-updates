# BGXAI — V2 weapon handoff, after Khalid game observation (19.11.2026)

## Reported observation
User game screenshot: Khalid attacked an enemy but did not switch automatically from ranged to melee. Screenshot alone does not prove whether attack was triggered by BGXRANGED or EPS. Do not infer installation state from screenshot.

## Actual code produced
- BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXRANGED_V2_MELEE_HANDOFF.baf
- BGXAI/patchsets/ranged_fighter_guarded_20261119/test_ranged_v2_policy.py
- BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXRANGED_V2_PREFLIGHT.py
- GitHub Actions workflow bgxai-ranged-v2-melee-source.yml; source/pysyntax checks PASS run 44483654759.
- **NO CHANGE TO LIVE GAME, BGXP5, BGX120 OR ONE-FILE CMD. V2 IS NOT YET INSTALLED.** Existing pinned menu 124 remains V1.

## V2 BAF behavior for pure fighter only (F guard ON)
1. Close hostile enemy within Range(...,4), fighter HP>75%, ranged selected: EquipMostDamagingMelee. No movement command.
2. Distant visible enemy outside Range(...,10), fighter HP>75%, melee selected and CanEquipRanged() (available ranged weapon+ammunition): EquipRanged. Gap between thresholds limits flapping.
3. Visible enemy with already selected ranged weapon in weapon reach but not within 4 ft: AttackOneRound.
4. Each block requires party member other than slot 0, Class FIGHTER only, F-guard LOCALS 1, BGX66 heal slot LOCALS 0, ActionListEmpty, ModalState NONE, no panic/helpless, HP>75%.
5. No autonomous melee attack is issued by V2 switch block; selection alone does not guarantee engagement. Old EPS may issue its own. No hazard-safe pathing, spell protection intelligence, manual order provenance, class hybrid roles. Automatic battle correctness **not proven**.

## Native read-only preflight draft
BGXRANGED_V2_PREFLIGHT.py accepts only exact pristine BDDEFAI (1170 blocks) with BGX120 last, OR V1 installed BDDEFAI SHA256 49b553908e7b66ab85714e91dd27800cad2ec4a9c51d8860d24aeb67b3c461b3 (1171 blocks) with BGXRANGED last, and confirms that subtracting first V1 block recovers SHA-pinned pristine BCS. Requires unchanged M_BX43.lua/PRIEST1.BCS. Compiles three new blocks with native WeiDU in TEMP and asserts that 1170 original blocks remain byte-for-byte at positions 4..1173. Fail closed on unknown current BCS. Needs actual live execution before deploying V2; its Python syntax passed CI but EET native V2 compilation is not yet proven.

## Next
Integrate safe preflight into single BGXAI_UPDATE.cmd without changing pinned installer/rollback behavior, run native preflight on user's EET, then prepare guarded WeiDU upgrade with backups and V1→V2 rollback. Only after explicit install consent conduct live combat: Khalid starts with bow and arrows, close foe prompts melee switch, retreating foe prompts ranged switch, confirm BGXP5 heal and manual command preservation. If enemy stands in Web do NOT treat this pilot as hazard-safe; do not test that until AoE observer is implemented.

## Update: one permanent updater menu 127 is ready (READ ONLY)

- Manifest `0.3.53-BGXRANGED-V2-NATIVE-READONLY` includes 5 SHA-pinned source files; V1 protected installer remains unchanged.
- Existing `BGXAI_UPDATE.cmd` now has 127: V2 native compile preflight (READ ONLY), supporting original baseline or V1 installed state; never install automatically.
- Immutable pinned BGXAI_SYNC.ps1 commit 42a54c0d69d7555dc0451deca8acc99bf1fdd0b6, size 79382, SHA256 b498c1453f738ec872cddd9428aafc9c923f9d821ccc87ba108c1e03157dfb36, pin update commit 0091a20a0902da45de8dcda5a8f141c11945b737.
- GitHub Windows PowerShell 5.1 AST + onefile SHA/menu 1–127 verification PASS on run 44484160978. The stand-alone V2 Python source test also PASS on runs 44483654759 and 44483866053.
- **Only next step on PC**: run existing BGXAI_UPDATE.cmd → 127, return full output. Do NOT run 124 to install V2: 124 still installs V1. No game changes made by this development update.
- Current stage: CODE yes; CI yes; native V2 compile in user game PENDING; V2 DEPLOY NO; V2 GAMEPLAY NO.


## 19.11.2026 — user native V2 PASS; guarded V2 install/rollback prepared

**Native result from user's own EET after choosing 127:**
- status=BGXRANGED_V2_NATIVE_PREFLIGHT_PASS
- current=V1_INSTALLED_1171
- candidate_sha256=1991f04d0a6acc556f53e03a7aa4a9fcaab252668b689f3d6726be118ca7c1e2
- source_sha256=dc08fa3a1e5d34463ecb984d1e2fdf2c2c8bc938bd36411f189ffc4f1d0a3eb0
- candidate_blocks=1173; preserved_old_blocks=1170; game_modified=false

**Committed and CI verified:**
- Independent V2 installer BGXRANGED_V2_GUARDED_INSTALL.py: exact V1 BCS/proof/WeiDU-last prerequisites; V2 source and candidate SHA pins; closes game/InfinityLoader; external SHA256 backup prior to staging; own BGXRANGED2 WeiDU component. No automatic retry.
- Its rollback requires BGXRANGED2 as last component and verified external backup; WeiDU restores V1 BCS, retaining old V1 component; status checks 1171 block V1 SHA and original code.
- Existing updater BGXAI_UPDATE.cmd **not replaced**; menu 128=V2 install (explicit typed INSTALL_BGXRANGED_V2_MELEE_HANDOFF), 129=V2 read-only status, 130=V2 rollback (explicit typed ROLLBACK_BGXRANGED_V2_MELEE_HANDOFF). Menu 124 remains old V1 installer: **do not use 124 for V2**.
- SHA-pinned release manifest 0.3.54-BGXRANGED-V2-GUARDED (6 source files), immutable BGXAI_SYNC.ps1 commit 5bbfbeda9267508a5144607e4f71928ad864f1a7; script 79929 bytes SHA256 15a73997bd4038f650a9f3e4cd8b7cca4fa07431ed97117af7ebfeb77e65100c; pin commit b654d1ecf06829b110c160115d47f61ee18ccc12.
- Windows PowerShell AST + all one-file source SHA/menu preservation CI run 44515423240 SUCCESS. Non-game V2 guarded installer mock regression run 44514829518 SUCCESS. Real native compile V2 in user's EET PASS. **V2 has not been installed**; no live gameplay verification of melee-switch.
- Current game's installed V1 unchanged by this development. Preserve BGXP5 healing, BGX120 AOE guard, manual commands and existing scripts.

**NEXT USER ACTION:** close game, InfinityLoader, WeiDU; run existing BGXAI_UPDATE.cmd; choose 128; only on intentional installation approval type INSTALL_BGXRANGED_V2_MELEE_HANDOFF. If successful, run 129 read-only and send output. For safe gameplay first check Khalid with both melee quickslot and bow+ammo, guard F on, HP>75, enemy inside 4ft (should equip melee), then enemy outside 10ft (should return ranged). Avoid Web/AoE and do not assume automatic melee attack or safe pathing from this minimal V2. If incorrect, do not chain further installs; use last-component guarded rollback 130 after inspecting status.

**Boundary:** V2 still pure fighter only; no multiclass/dual logic, 3E thief flanking, mage retreat, magical immunity evaluation, full AoE safety or confirmed manual-order provenance. These remain approved goals, not installed features.
