# BGXAI R13 — REAL LIVE COMBAT 2026-11-23: three DEFENSE events, all HOLD

**Source**: actual user-uploaded `BGXAI_R13_CONSOLE_20261123T061617028509Z.log`, 388 lines, 233237 bytes; initial file presentation said 389 lines, complete mounted file read: 388 newline-split lines. User described: first fighter attacked, was critically hurt, withdrew; second approached and fought. This is valid, sufficient real test. **Do not ask user to repeat battle**.

## Verified runtime events
- `[BGXTD13]` exactly one SESSION at line 50; exactly one READY hookRegistered=true line 51.
- Exactly three DEFENSE events, all status **HOLD**, nine defense fields all null: line 159 partyIndex 2 seq1, line 233 partyIndex 1 seq2, line 339 partyIndex 2 seq3. All q data fields sourceActor, targetActor, selectedSlot, selectedAbility, rawActionId null **because HOLD output excludes extra**, not proof EEex gave null values.
- Cross-check R1/R4:
  - actor ID 139266124 (partyIndex2): BGXW4 and BGXWP ACTION with `actionRaw=3` and `selectedWeaponRaw=12` at lines 162–165 and 342–345; BGXFTRACE shows target actor 135137293.
  - actor ID 139200587 (partyIndex1): BGXW4 & BGXWP `actionRaw=3` and `selectedWeaponRaw=10` at lines 236–238; FTRACE also has actor party targeting in another `actionRaw=31` event. The user switching party actors is visible, but game log does not independently certify health/wounds.
  - BGXW4 also extracted all 68 selected source stat fields with missingCount=0 in related events. This does **not** imply R13 target defense read is successful.
- No R13 target defense readings successful. **R13 LIVE registered and called; TARGET DEFENSE LIVE=HOLD. Weapon auto switch prohibited.**

## Verified code defects — fix source-only before any more testing
In `BGXAI/patchsets/ranged_fighter_guarded_20261119/M_BGXD13.lua`:
1. Core.inspect() initially requires `int(ctx.selectedSlot,11,38)`. `selection()` further requires slots 35–38 (quick weapons) or 11–14 (ammo). A real started attack (partyIndex1) uses `selectedWeaponRaw=10`: deterministic `CONTEXT_INCOMPLETE` even before the target is inspected, due to rejecting slot10. **Don't change ranges without checking EEex native equipment semantics**; this is a read-only safety gate, not permission to choose weapons.
2. R13 output(status, reason, extra) carries `reason`, but runtime `event_json(q,partyIndex)` serializes only `status` and `rawFields`, dropping the `reason` on HOLD. This hides why partyIndex2 (slot12) also held. Add safe escaped bounded `reason` to runtime logs and relevant read-only raw actor/target/slot observations before assessing why target lookup fails; do not leak personally identifying/game chat text.
3. `sourceActor`, `targetActor`, `selectedSlot`, `rawActionId` serialize from `q` only; HOLD output has none, so nulls reflect the **output schema bug** not proven missing native values.
4. EEex `m_selectedWeapon=12` is ammo slot, while 10 was also observed; selection code needs a documented mapping and safe snapshot. Preserve no-queue/no-dispatch policy.

## Next
**No user actions now; no more fights/reinstalls.** Safe local task is build a source-only read-only diagnostic patch for R13 that records HOLD reasons and candidate raw source/target/slot, with tests for slots 10 and 12, and existing installs preserved. Deployment requires separate typed consent and its own preflight/backup/WeiDU last-only verification. Never claim R13 target defense succeeded or weapon switching authorized. Any unrelated UI menu parse error `']' expected near 'icon'` is separate and should not be conflated.
