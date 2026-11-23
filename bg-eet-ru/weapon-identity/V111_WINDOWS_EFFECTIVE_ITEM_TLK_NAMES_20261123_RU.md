# BG_EET_RU — V111 actual Windows ITM/TLK names confirmed (2026-11-23)

## Verified source and data level
User's canonical report upload `SEND_TO_CHATGPT_BG_EET_RU(20261123-142938).zip` was verified offline: 808381 bytes; SHA256 `24e7e2425f4d8a38cb275def0ba0e555cd4be62382ff9b8fe7db5de0cc8b5339`; 126 unique entries, ZIP CRC PASS. `55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json`: `updater_version=111`, `V111_THREE_LOCAL_ITEM_NAMES_EXTRACTED_READONLY`, `resolved_identified_names=3`, errors empty and `game_files_written=0`. This is Windows read-only local data verification, not live UI name display proof.

**Active item resources and exact Russian names from installed `lang/ru_RU/dialog.tlk`:**
- **`SW1H04`** from installed `override/SW1H04.ITM` (SHA `73e3de6a07afc42f50d63b74c3235c1f9efdd773e280c501b481e876647eda88`), ITM type **20** (`LARGE_SWORDS`). Unidentified StrRef **2893** “Длинный меч”; identified StrRef **6741** “Длинный меч”.
- **`AROW01`** from `chitin.key` → `data/Items.bif` (SHA `52209dceddf99fec75e20a694b42906fa3f9ea74c6cacad5d62d33eff22f9d91`), ITM type **5** (`ARROWS`). Unidentified StrRef **6328** **“Отличная стрела”**; identified StrRef **6759** **“Стрела”**. Preserve this difference, do not automatically treat all arrows as “Стрела” without runtime identification evidence.
- **`BOW05`** from `chitin.key` → `data/Items.bif` (SHA `0bfc6680b759239052dcd1882a1d2f354e7bc840e535f0b9499a5c7a3c07d797`), ITM type **15** (`BOWS`). Unidentified StrRef **6864** “Короткий лук”; identified StrRef **6865** “Короткий лук”.

All six StrRefs match `lang/ru_RU/dialogf.tlk` as well. Current RU dialog TLK SHA `792b109b68f368bc205a543f7bbf242d958b8d029d80e9be525547a3c6193ef1`, dialogf SHA `a2f3fb773ca0e042ce6188af75d525177b3b24acfb0b2b9d4aa019eeb5b4d672`.

## Runtime identity evidence still preserved
The new ZIP `54_V108_NATIVE_ITEM_RESREF_PILOT.json` has default `mode=status` and `V108_INSTALLED_AWAITING_NATIVE_RESREF_CAPTURE`; historical console evidence is retained: two actual V108 callback records `weapon_resref=AROW01` plus `launcher_resref=BOW05`. Earlier separate capture had `weapon_resref=SW1H04`. Thus **effective item identity and Russian resource names both confirmed**, but not a single UI journal row correlation or miss-path identification.

## Consequences and next milestone
- **Verified:** `V108 damage context → exact CItem RESREF → actual installed EET ITM source → item type and local RU string`. V111 made no game changes.
- **Still HOLD:** matching same combat event to a unique BRIEF/FULL journal row; attack attempt / misses (existing damage observer does not demonstrate these); how unidentified names should display live. Existing V86 source-only demonstrated parsing a screenshot-like Russian text line `Халид: бросок атаки 2 - 1 = 1 : промах`, but NOT a live callback: `V86_STATIC_UI_FEASIBILITY_CAPTURED_NO_LIVE_HOOK`. Never cite this as weapon identity for misses.
- No new EEex hooks, no invasive injection or game write. Preserve V108 installed, V101 FULL/BRIEF, BGXAI, BG Voice RU, UI, TLK, EXE, saves. Do not repeat V108 gameplay tests or V111 ITEM scans without new reason.
- Next engineering task: inspect **existing** combatLog/EEex display-message paths and their stable event identifiers, build an offline-safe read-only correlation proposal before altering installed UI. A timestamp/actor alone is not guaranteed unique when APR, multiple attackers or simultaneous projectiles are involved. No auto-install.

Private user ZIP and raw console logs are NOT published to GitHub. Complete private offline reports `BG_EET_RU_V111_WINDOWS_NAMES_AUDIT_20261123.json` and handoff `BG_EET_RU_V111_WINDOWS_NAMES_HANDOFF_20261123.md` archived in Library.
