# BG_EET_RU — V105 LIVE event-context evidence (2026-11-23)

## Actual user-observed gameplay

EET engine 2.6.6.0; active V105 observer; game via InfinityLoader. User's console screenshot after a ranged attack:

* `OBS=true IO=false` — callback registered, standard file writing unavailable.
* `V105 EVENTS=3 BUFFER=3` — live base-weapon-damage callback was invoked three times and buffered three events; **does NOT prove three distinct hits**.
* Screenshot of `V105 FIELDS` for event 1:
  * `ability:userdata`
  * `attackRoll:number`
  * `attacker:userdata`
  * `effect:userdata`
  * `isCritical:boolean`
  * `isLeftHand:boolean`
  * `target:userdata`
  * `weapon:userdata`

Another screenshot shows Khalid's bow critical hit against a sick gibberling: 12 missile damage. Screenshot alone does NOT match this exact combat-log line to any one of the three buffered events.

## Confirmed implementation facts

V105 observer only records primitive field values and type labels in `events[].fields`; it does not retain raw userdata. Therefore weapon RESREF, ammo, creature names cannot be retroactively obtained from V105 buffered events. Never instruct the user to dereference `events[1].fields.weapon` as though it held CItem; it only holds `{value_type="userdata"}`.

EEex upstream source `EEex_Sprite.lua` documents `EEex_Sprite_GetLauncher(sprite, curAbility)`, and the user-supplied V104 archive SHA evidence confirmed launcher API in their actual EEex build. Source-based structural docs for x64 `CItem` show `CItem.baseclass_0` as `CResHelper<CResItem,1005>` with `cResRef` at offset +8. Any live read must be restricted to an actual valid callback's CItem object and tested/guarded, never dereference a stale userdata pointer from an archived event. Do NOT conflate launcher and projectile; need separate evidence and special-case testing for throwing weapons.

## Next implementation gate (SOURCE ONLY until explicitly approved)

1. Prepare replacement V106 observer in source-only branch; preserve exact V105 installation baseline. It must not install automatically.
2. Try `Infinity_Log` only if function exists (verified in separate BGXAI workflow). Bounded logs with prefix `BG_EET_RU_V106` and no effect/context mutation; unknown values remain unknown.
3. Validate live callback-provided `weapon` / `ability` types with defensive typed-access and tests; collect real resref within callback, not after. Do not call native EEex launcher helper until the exact ABI/ability type is confirmed.
4. Avoid `io.open` (unavailable in this runtime). Reuse one `BG_EET_RU_UPDATE.cmd` and one `SEND_TO_CHATGPT_BG_EET_RU.zip` for capture/import. Preserve full journal and existing V101.
5. Before any game modifications, require exact SHA of V105 installed Main/module, external backups, graceful rollback, closed game, and typed approval.
6. Live test must separately demonstrate weapon and ammunition identity for hit and miss before activating brief-journal labels. Damage callback has not been proven to cover misses.

No game writes done by this checkpoint. V105 installed on user's system; V106 not installed, not gameplay-verified.
