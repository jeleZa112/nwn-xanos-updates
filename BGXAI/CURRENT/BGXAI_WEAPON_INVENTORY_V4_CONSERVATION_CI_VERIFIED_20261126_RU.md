# NEXT VERIFIED STAGE — 26.11.2026: XEquipItem REAL ENGINE ACTION IN INERT NATIVE SOURCE PROBE

**This supersedes older next-step instructions below, not their historical evidence.** IESDP BGEE: actual action `385 XEquipItem(item,object,slot,EQUIP)`, `CheckItemSlot` tests exact source, `!HasItemSlot` tests empty target, `ActionListEmpty` idle check, `CombatCounter(0)` indicates no combat but may be inaccurate in particular cases. `SLOTS.IDS` source 18..33 => `SLOT_MISC3..18`, destination 35..38 => `SLOT_WEAPON0..3`; `XEQUIP.IDS EQUIP=1`. These are documented mechanics **not native EET behavior/proven item conservation**. Never use `FillSlot`, `Stop`, `ClearActions`.

**New CODE**: `BGXAI/BUILD/WEAPON_XEQUIP_NATIVE_INERT_PILOT_V1_20261126/BGXAI_XEQUIP_INERT_PROBE_V1.py` generates `IF False()` one-action **inert** BAF with source/destination/party/idle/one-shot LOCALS guard; no game installation or action. `BGXAI_XEQUIP_NATIVE_PREFLIGHT_RO_V1.py` reuses **existing** temp WeiDU backend pinned by Git blob SHA `0bd66e6f2fd97cf69291a7b3ae5463f7e3295995`, defaults source-only. Its optional separate native-readonly invocation is **not exposed in user's BGXAI_UPDATE.cmd yet** and has NOT been run on EET. No second CMD/PowerShell or live file written.

**REAL CI**: [45771911979](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45771911979) **SUCCESS 11/11 Python tests** for impossible-to-activate BAF; [45772130570](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45772130570) **SUCCESS 11/11 source tests + 9/9 pinned backend tests**, no game accessed. Job logs verified, no native EET compile.

**BLOCKER**: existing `BGXAI/BGXAI_SYNC.ps1` = **79,832 bytes**, user onefile size ceiling **80,000 bytes**. DO NOT just append menu175 and break bootstrap; need audited safe refactor/source-only integration with byte cap and Windows PS5.1 AST + existing menu174 regressions, preserve single pinned `BGXAI_UPDATE.cmd`. Next real player step only AFTER that is complete and automatic notification has a concrete requested safe action. Do not ask user to run a new tool, repeat Khalid fights or perform manual Lua edits now.

**CURRENT STATUS**: BAF CODE yes; source-only CI PASS; **native compiler against user's EET UNKNOWN; game DEPLOY NO; game LIVE NO; safe autonomous equipped-instance move NOT WORKING YET.** Existing V6/R29/R37 game behavior preserved; no game, localization, EPS, saves or updater changed.

---

# BGXAI — Weapon Inventory priority V4 + conservation V1 — VERIFIED SOURCE CI — 26.11.2026

## MOST RECENT P0 STATUS — continue from HERE

**Actual feature goal:** when a party member holds a situation-appropriate weapon in the backpack, choose it using the already implemented V3/V4/V5 target-relative scorer and, after game-native safety proofs, **equip from inventory into an empty class-permitted quickweapon slot without interrupting an existing attack, EPS or manual command**. Do not rewrite existing V6/R29 bow→sword mechanism or spend time on redundant passive observers.

**CODE/TEST accomplished this turn:**
1. Confirmed existing **single listener R37 + corrected 16-slot backpack INV3** integrated source, original R33/R37 outputs preserved, 0 orders. CI [run 45770227906](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45770227906) **completed SUCCESS**, real logs: Lua5.3/5.4/LuaJIT each say `BGXAI corrected backpack V3 13 mock tests PASS` and `PASS R37+INV3 source-only ONE listener, 7 transitions, original R33/R37 logs, 0 orders`; static Python PASS. This replaces prior statements "full combined runtime test unverified" for that exact source commit; not game runtime.
2. Created new **V4 corrected inventory weapon-choice planner**:
   - `BGXAI/BUILD/WEAPON_INVENTORY_PRIORITY_V4_20261126/BGXAI_BACKPACK16_PRIORITY_RO_V4.lua`, test, README, workflow `.github/workflows/bgxai-backpack16-priority-v4-source-ci.yml`.
   - Reuses V1 scoring margin and V3/V4/V5 external evidence contract, but **corrects backpack to slots 18..33** and excludes quick item slots 15..17, magical weapon 34. Checks full available top-level equipment items 0..17/34/35..38 for same resref and an EMPTY permitted destination, preserves action context, never overwrites, HODL if opponent or effects unproven.
   - [GitHub Actions 45770826868](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45770826868) **completed SUCCESS**; verified job log contains `BGXAI BACKPACK16 PRIORITY V4 20 synthetic tests PASS` under **Lua5.3, Lua5.4 and LuaJIT**. Test cases include no-overwrite, duplicate in shield, quickitem, magic weapon, quiver, occupied quickweapon, 2-slots class, curse, ammo/launcher, effects, target same area, previous V1 20-cell bug. All results `executable=false`, `inventoryMoveAuthorized=false`.
3. Created **V1 strict top-level item conservation postcondition validator**:
   - `BGXAI/BUILD/WEAPON_INVENTORY_CONSERVATION_V1_20261126/BGXAI_TRANSFER_CONSERVATION_RO_V1.lua`, tests, README, workflow `.github/workflows/bgxai-weapon-transfer-conservation-v1-ci.yml`.
   - Checks before/after **same-session** ordered snapshots of actor top-level item slots 0..38. For proposed source 18..33 and destination 35..38, requires unique resref, originally empty target, after source EMPTY, destination exactly same resref/flags/3 charge counters, no other slot altered. Fail closed on cross-actor, stale or reversed time, missing item, duplicated/lost item, changed charge/shield/ammo, incomplete map. This is a *post-action oracle*, NOT active dispatch or rollback.
   - [GitHub Actions run 45771058355](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45771058355) **completed SUCCESS**. Actual job logs: `BGXAI item conservation 19 pure model tests PASS` for Lua5.3, Lua5.4 and LuaJIT, grep denylist for any active engine action PASS.
4. Historical **V2 backpack bridge** is superseded, its original [CI 45765546692](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45765546692) **FAILED** in mock `unverified item` assertion even after regex fix. Old V1 used wrong 15..34 range. Do NOT re-use V1/V2 or claim their CI green. The corrected V3/V4 path is new authority.

## Hard safety boundaries unchanged
- EET + SCS35.21 + EEex1.1.7 + EPS18.4 on Insane. Installed V6/R29/R37 remain untouched. R37 LIVE 12/12 refers to older installed read-only action callback, not new Inventory V3/V4. New install/live status **NO**.
- `BGXAI_UPDATE.cmd` is only user-facing launcher; no auxiliary CMD/PowerShell. No game, save, Lua live override, TLK, BG Voice RU/BG_EET_RU modifications performed by these GitHub commits.
- IESDP BGEE action 385 `XEquipItem(S:Item*,O:Object*,I:Slot*Slots,I:EquipUnEquip*Xequip)` is available, but **not proven to move a specific item instance, preserve all charges in THIS EET, act only at idle boundary, or be safe for EPS/manual orders**. `EquipItemEx` *does not move* the item, and `FillSlot` can destroy its occupant. No active equip dispatch until actual controlled game semantics and safety proof. See https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm and https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm .
- V4 currently receives externally supplied score/provenance. Its offline `*Verified=true` flags must NOT be passed off as real current EET engine evidence, and its duplicate scan only covers complete top-level map, not items inside containers. V1 postcondition verifies simulated data, not observed game action.
- No `Stop`, `ClearActions`, manual/EPS queue rewriting, new weapon selection interrupt. Already committed arrows in 6-second round should not be cancelled.

## Exact next feature engineering gate (not old diagnostics again)
1. Determine **actual EET XEquipItem semantics** and safest action boundary, using current official game docs and prior EEex/scripting evidence; if still uncertain, prepare a **single reversible pilot** for an item actually proven in a character's backpack and an EMPTY allowed quickslot, on a disposable save only. Must use original `BGXAI_UPDATE.cmd`, SHA-pinned script, external backup, WeiDU last-only, and explicit user typed consent; do not install from offline CI PASS.
2. Prepare a native compile-only preflight against installed EET ACTION.IDS/SLOTS.IDS/XEQUIP.IDS and existing WeiDU, with exact candidate resref (no fabricated RAM identity), proof of safe item type/skill/kit, EPS/manual arbitration, and postcondition observer to establish preserved items, charges, other slots and original action.
3. After real safe equip is shown, connect **existing** V3/V4/V5/effects/proficiency and target immunities into the request producer, not a second scoring implementation. First empty slot; full occupied-slot swaps only separately with a safe return path.
4. If any resource provenance/queue state is unknown, KEEP_CURRENT and do not dispatch. Record status as HOLD with reason, never advance on a false "verified" bit.

## Four-tier result
| Component | CODE | TEST | DEPLOY | GAME LIVE |
|---|---|---|---|---|
| R37 + INV3 candidate | yes | Lua53/54/LuaJIT CI SUCCESS | no | no |
| Inventory priority V4 | yes | 20/20 x3 CI SUCCESS | no | no |
| Item conservation V1 | yes | 19/19 x3 CI SUCCESS | no | no |
| Actual backpack→quickslot auto-equip | no | no | no | no |
