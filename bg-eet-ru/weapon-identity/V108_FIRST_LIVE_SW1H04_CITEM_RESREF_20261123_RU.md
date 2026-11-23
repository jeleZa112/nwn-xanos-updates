# BG_EET_RU — V108 FIRST LIVE CItem item resref from user game (2026-11-23)

## Windows proof, preserved without publishing private ZIP
- User's newest submitted canonical ZIP (2026-11-23 11:37:46 filename timestamp) passed integrity check: **125 entries, unique, CRC PASS**.
- SHA256 `5db3cf19d88f5fa9a213565cb202dc5722da81021274da9bf5056c3c98587be0`.
- `54_V108_NATIVE_ITEM_RESREF_PILOT.json` has `updater_version=110`, `mode=capture`, `status=V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED`, `errors=[]`, `game_files_written=0`, `event_lines=2`.
- Two native callback V108 events: ordinal **1** `weapon_resref=SW1H04`, `launcher_resref=NOT_CITEM_USERDATA`; ordinal **2** same. The logged `ammo=UNVERIFIED`, `hit_miss=UNVERIFIED`, `journal_row=UNVERIFIED` remain unchanged. The full raw game console and user ZIP are NOT published.
- This is **LIVE PASS for native `CItem.cResRef:get()` returning real data in the user's installed EEex while damage callback executed**. It is NOT full weapon/ammo identity coverage, not proof of a miss listener, and not combat-log row correlation; original report flags `resref_verified=false`, `gameplay_verified=false` remain rightly conservative.
- Independent canonical BG item references identify `SW1H04` as ordinary `Long Sword` (Russian descriptive equivalent «Длинный меч»), e.g. https://baldursgate.fandom.com/wiki/Long_Sword and https://baldursgate.fandom.com/wiki/GameFiles/ListItems . In *modded EET* the current local `ITM/TLK` label is not verified; never force this label into FULL or BRIEF from public wiki alone.
- Only **2 melee-like events** seen in this capture; absent `launcher` here does NOT prove the user did not fire a bow (the callback is damage-related and can omit misses or some combat paths). No bow/ammunition event can be validated yet. The prior V106 historical 2 events remain preserved and were not repeated.

## Next restricted action
- If the user **did not** fire a bow yet, a single focused in-game test using **already installed** V108 with the **same** `BG_EET_RU_UPDATE.cmd --capture-v108-native-read` can obtain a bow/arrow event after one or two **damaging** ranged shots; game must be closed before launching capture, then fully exited before ZIP export. Reinstall and old V106 capture are unnecessary.
- If user **did** fire a bow in this capture, do not request blind repetition: first check what happened (missed, projectile hit, console result) and whether the routed game process captured until exit.
- Do not install any extra observer, alter game/UI/TLK/V101 FULL-BRIEF/BGXAI/Voice/saves, or publish user private files.
- Keep SOURCE, LIVE single-field read, gameplay, and item labeling statuses separate. Project private notes/audit saved to Library /BG_EET_RU/CURRENT/BG_EET_RU_V108_LIVE_HANDOFF_20261123.md and BG_EET_RU_V108_LIVE_CITEM_AUDIT_20261123.json.
