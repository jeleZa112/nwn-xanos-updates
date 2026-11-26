# BGXAI — after-action equipment conservation validator V1 (26 Nov 2026)

Pure Lua source-only postcondition validator; it receives COMPLETE top-level item maps of slots 0..38 observed before/after an independently issued engine action, including corrected backpack slots 18..33 and quickweapon 35..38, plus candidate source/target/resref. It requires that the unique item leaves only its backpack cell, appears unchanged (resref, flags, 3 charge counters) in an initially EMPTY permitted quickslot, and that no other top-level slot changes. Any loss, duplicate, modified charges, already-occupied destination, unexpected shot or change, unreadable slot or wrong actor => HOLD.

**Nothing here executes XEquipItem**, registers a listener, changes a game file, clears a queue or authorizes rollback. Even perfect synthetic matching returns `engineTransferSemanticsVerified=false`, `liveEvidenceVerified=false`; this code only defines a strict check for future real bounded GAME A/B. Other container contents and hidden equipped state not part of 0..38 cannot be proven by this validator. The real game should be backed up and a disposable save used, with typed explicit permission and one existing updater; CI PASS cannot be read as deploy permission.

Based on IESDP BG(2)EE action `385 XEquipItem` (not unique instance) and actual 16 backpack slots `18..33`. Do not use `FillSlot`, as it can destroy an existing target item; `EquipItemEx` does not move the item.

CODE: V1 generated. TEST: `test_transfer_conservation_ro_v1.lua` 16 synthetic cases, independent GitHub Actions needed. DEPLOY NO, LIVE NO.
