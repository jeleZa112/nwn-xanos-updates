# VERIFIED SOURCE CHECKPOINT — 26.11.2026

**CODE + OFFLINE CI TEST PASS. STILL INERT, GAME NOT CHANGED.**

New `BGXAI_XEQUIP_NATIVE_PREFLIGHT_RO_V1.py` is not a second updater: it imports and SHA1-Git-blob-pins the **existing** `BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py` (blob `0bd66e6f2fd97cf69291a7b3ae5463f7e3295995`). Default mode only checks the generated `IF False()` BAF and template; native mode is explicitly opt-in and, when later exposed in the single updater, will perform **temporary read-only WeiDU compilation** with source-byte check and watched-file pre/post hash comparison. No install, no game action, no new PowerShell/CMD.

**Confirmed real GitHub Actions:**
- [Run 45771911979](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45771911979) source-only inert BAF generator tests: **11/11 PASS**.
- [Run 45772130570](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45772130570) same generator **11/11 PASS**, pinned shared preflight contract **9/9 PASS**, default source-only no-EET proof **PASS**. Results inspected in job logs.
- `BGXAI_SYNC.ps1` on branch at 79,832 bytes, current onefile limit 80,000: **DO NOT append a menu without safe size reduction/refactor and Windows PS5.1 AST/pinned SHA regression.** Existing menu174 R37 remains untouched. Do not recommend a separate launcher.
- No native WeiDU compile against user's actual `C:\Games\BG_EET_FOXX_NEW` has been performed for this BAF. `XEquipItem` action behavior still NOT VERIFIED. This sample `HAMM01` is illustrative and is not proof of an item actually in user's backpack. Any actual game test needs separate typed consent, disposable save, native IDs, instance uniqueness, source/target actual proof, EPS/manual arbitration and postcondition conservation.
- **EET installed components V6/R29/R37, EPS, BG_EET_RU, BG Voice RU, UI, saves, .cmd remain unmodified.**

## Next single-updater engineering gate
Integrate this RO source probe as a subcommand of the EXISTING onefile after preserving pinned bootstrap and 80k boundary; source-only menu exposure may be offered for user's action only after exact Windows PS5.1 tests and no-live-writes proof. Then on user's game verify native ACT/TRIGGER/SLOTS/XEQUIP IDS compile with known WeiDU binary SHA, without executing a script. Only later separately prepare an actual disposable SAVE game A/B with strictly scoped typed install and last-only rollback.

---

# BGXAI XEquipItem — INERT native compile probe V1 (2026-11-26)

**THIS IS NOT A NEW GAME MOD AND NOT AN ACTIVE EQUIPMENT PILOT.** Source-only compiler input builder; no game file changes, one updater unchanged. The generator produces exactly one BAF `IF False() ... THEN ... XEquipItem(...) END` for a validated manifest. `False()` is mandatory and unconditional: even accidental loading cannot arm the action. The input manifest is a SYNTHETIC SAMPLE (`HAMM01`), NOT proof that the item is in Khalid's backpack. The compiler has NOT run against the user's real EET, so `nativeWeiDUCompileVerified=false`.

## Technical basis
IESDP BGEE `ACTIONS.IDS` action **385** signature: `XEquipItem(S:Item*,O:Object*,I:Slot*Slots,I:EquipUnEquip*Xequip)`. `XEQUIP.IDS` `1 EQUIP`, `0 UNEQUIP`. `SLOTS.IDS`: `18..33 SLOT_MISC3..18` (16 true backpack), `35..38 SLOT_WEAPON0..3`. `TRIGGER.IDS`: `CheckItemSlot(Myself,"HAMM01",SLOT_MISC3)` proves source presence; `!HasItemSlot(Myself,SLOT_WEAPON1)` guards empty target. Additional checks: `ActionListEmpty()`, `CombatCounter(0)`, `Global("BGXWI1GO","LOCALS",1)`, no active magic cooldown. *None* of these proves an atomic action boundary or manual/EPS ownership.

## Next safe technical gate
**Reuse** `BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py`'s established temporary WeiDU pattern; do not rerun old V3 tests. Stage BAF only under external temp, pin exact generated SHA, choose verified WeiDU `setup-enhanced-powergaming-scripts.exe` SHA 0d17e26e..., require real `chitin.key`, original EET dialogue language, no modifications to `override`/`WeiDU.log`, read-only before/after watched file hashes. Native preflight shall verify symbols `SLOT_MISC3`, `SLOT_WEAPON1`, `EQUIP`, `XEquipItem`, `CheckItemSlot`, `HasItemSlot`, `ActionListEmpty`, `CombatCounter`. Still NO install.

Later only after separately authorised **typed** pilot: prepare a disposable save, real item unique resref in proven source slot, 1 empty quickslot allowed by class/kit, preserve original current action, prevent EPS/manual overrides, run real game and audit before/after with `BGXAI_TRANSFER_CONSERVATION_RO_V1`. Any ambiguity => HOLD. Do NOT ever deploy this inert `False()` code as claimed game functionality; active BAF generation requires a separate audited revision.

## Evidence links
- https://iesdp.bgforge.net/scripting/actions/bgeeactions#385
- https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm
- https://burner1024.github.io/iesdp/files/ids/bgee/xequip.htm
- https://burner1024.github.io/iesdp/scripting/triggers/bgeetriggers.htm#0x4103
- https://burner1024.github.io/iesdp/scripting/triggers/bgeetriggers.htm#0x40B2

**CODE** generated; **TEST** must be verified by GitHub CI; **NATIVE COMPILE/DEPLOY/LIVE NO**.
