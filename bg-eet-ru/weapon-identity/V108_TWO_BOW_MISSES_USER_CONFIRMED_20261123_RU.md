# BG_EET_RU V108 live capture — user explained two bow misses (2026-11-23)

## User-confirmed sequence
In the test that yielded two real V108 records `weapon_resref=SW1H04` and `launcher_resref=NOT_CITEM_USERDATA`, the player **fired two bow shots, both MISSED**, then **switched to sword and shield**. No user report of a successful bow hit in that capture.

## Interpretation and limitations
- V108 hooks `EEex_Sprite_AddAlterBaseWeaponDamageListener`, a **base-weapon-damage** event, not a universal attack-attempt/miss listener. Missed shots are expected to be absent from that damage callback; this matches the observed two sword-derived events.
- The two `SW1H04` lines establish item RESREF reading in the existing modded game within callback, but do not individually identify the shield (not part of the recorded fields), nor prove every sword swing/strike is captured.
- Do **not** diagnose bow support as broken from this sample. No bow projectile RESREF, launcher RESREF, ammo RESREF, or miss-to-journal mapping has yet been demonstrated.
- No need to repeat old V106/V107, reinstall V108, or change combat/UI/TLK. For the next bounded live capture, focus **only on ranged attacks that actually deal damage** to a vulnerable target. Use the existing single updater `BG_EET_RU_UPDATE.cmd --capture-v108-native-read`; ensure the game and loader are closed before launching it, then completely exit and send the canonical single ZIP. Do not infer a hit merely from `attackRoll`; compare direct damage in game.
- For full combat-journal coverage including misses, research a separately verified attack/hit roll hook source-only. Do not install a speculative hook; preserve V108 until ranged-hit evidence.

Evidence: user's explicit textual clarification in this chat; no private ZIP published.
