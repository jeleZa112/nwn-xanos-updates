# BGXAI — first actual **armable** XEquipItem script SOURCE ONLY, V2

This advances beyond the previous `IF False()` compiler exercise. It generates a real one-shot game BAF that **could** move a held item if installed and later explicitly armed. **No game files were installed, no arming, no dispatched action** in this phase.

BAF guards: exactly one NPC party position, `ActionListEmpty()`, `CombatCounter(0)`, no spellcast/helplessness/panic, `CheckItemSlot(Myself,"RESREF",SLOT_MISC3..18)`, `!HasItemSlot(Myself,SLOT_WEAPON0..3)`, and `Global("BGXW2ARM","GLOBAL",1)`. One response **first changes Global to 2 and actor LOCALS attempt to 1** (one shot), then invokes `XEquipItem(...,EQUIP)`. The generated BAF does NOT set arm=1 or modify attack queue. A manual/engine interruption after guard evaluation is still possible: **do not use in active combat** and never assume these triggers prove EPS/manual arbitration.

**Input manifest example is FAKE**. It uses `SW1H04` and an all-'a' SHA but does not prove the item is in backpack or the target is empty. A positive build is only `ARMABLE_BAF_SOURCE_NOT_INSTALLED_NOT_AUTHORIZED`, never authorisation. Need actual read-only actor inventory snapshot, unique resref across all top-level slots 0..38, class permitted quickslot, expendable safe nonquest item, independent backup/disposable save, engine-native compile of this exact BAF, and separate human typed approval. No auto-install/rollback/console commands exist in this module.

Historical R29 BCS merge provides reusable byte-preserving `bcs_parts` pipeline; V3 inventory and V1 postcondition provide strict data and conservation contracts. Next engineering task: native source-only merge/test against the current protected BDDEFAI baseline and verify no legacy block changes, then propose a guarded one-time WeiDU pilot, **without installing or touching EPS/V6/R29/R37**. Failure of any evidence must HOLD and keep the game unchanged.

Reference BG(2)EE IESDP: action 385 `XEquipItem`, triggers `CheckItemSlot`/`HasItemSlot`, `SLOTS.IDS`. This command's runtime inventory transfer semantics and current action preservation are **not yet proven in user's EET**.

CODE = new armable game BAF *builder*; TEST = local/CI synthetic only; DEPLOY NO, GAME LIVE NO.
