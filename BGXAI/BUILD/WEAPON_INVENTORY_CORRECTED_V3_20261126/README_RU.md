# BGXAI BACKPACK 16 — CRITICAL CORRECTION V3 (26.11.2026)

**SOURCE ONLY / NOT INSTALLED / NO ACTIVE ITEM MOVEMENT.**

## Root cause
V1 incorrectly assumed all 20 slots 15..34 were backpack items. In BG(2)EE: 15–17 quick items, **18–33 the 16 true backpack cells**, 34 magical weapon slot. `ITMSLOTS.2DA` listing extra 44–47 belongs only to **PSTEE**, NOT BG(2)EE; it was wrongly cited in an earlier response. Verify via IESDP CRE V1 Item Slots: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm and BGEE slots IDS: https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm. Modded EET actual layout is not runtime-proven by public documentation; independent live preflight required before moving any item.

## Supersession
- V1 `BGXAI_WEAPON_INVENTORY_PREP_RO_V1.lua` and V2 `BGXAI_R37_BACKPACK_BRIDGE_RO_V2.lua` remain in GitHub as **HISTORICAL / INVALID BACKPACK LAYOUT FOR EXECUTION**. Their source-only synthetic test PASS says nothing about a correct equip transaction. Never enable their proposals for dispatch.
- V3 `BGXAI_BACKPACK16_R37_RO_V3.lua` reads exactly 18..33, returning raw resref/flags/count, with fail-closed unreadable state; refuses to treat slots 15–17 or 34 as backpack. It runs two reads inside one function; a typed contextReader must reproduce original R37 action/selection/queue/script values both before AND after. If these drift, HOLD. Even if they don't drift, **safe action boundary and manual/EPS origin remain UNVERIFIED**. Nothing sends orders.
- V3 does not register an EEex listener; not yet attached to installed R37. It does not construct trustworthy alternative APR, ITM effects, class/kit rights, target resistances, unique item identity or `XEquipItem` transaction. `R37.currentScriptNumberRaw` only a number, not script ownership. No action queue clear/cancel.
- `test_backpack16_r37_v3.lua` covers correct mapping, postread action/queue changes, same resref duplicates, raw drift, invalid item, broken read, forbidden quick/magic slots, no orders. Tests are synthetic and **not live**.

## Required gates
1. Exact Lua source tests on 5.3/5.4/LuaJIT + CI denylist with selftest; verify results instead of asserting PASS on file creation.
2. Source-only R37 composition (same listener) using actual verified postcontext reader without changing R33/R37 event logs. Ensure action/queue read API matches installed EEex.
3. Inventory scanner needs engine-side whole item identity/provenance to safely address a unique resref; `XEquipItem` syntax does not prove atomic move/collision behavior. First pilot only empty **permitted** weapon quickslot, no items lost or charges changed, backup/WeiDU last-only + typed consent.
4. Only after conservation+manual/EPS boundary proofs can source be staged via existing `BGXAI_UPDATE.cmd`; protect all installed V6/R29/R37 and foreign project files.

CODE: V3 exists. TEST: until completed runs are verified => NOT VERIFIED. DEPLOY/LIVE: NO.
