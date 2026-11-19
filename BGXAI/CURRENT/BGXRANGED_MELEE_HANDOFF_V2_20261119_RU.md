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
