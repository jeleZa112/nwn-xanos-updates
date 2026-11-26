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
