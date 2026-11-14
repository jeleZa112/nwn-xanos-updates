# BGXAI 076 — проверенная настоящая 066S; приоритеты BCS на анализ

Дата: 2026-11-14. Проект BGXAI / пользовательская EET Foxx (сборка 05.11.2026), SCS 35.21, EPS 18.4, EEex 1.1.7, Insane.

## Новый настоящий результат пользователя, НЕ синтетический

Пользователь запустил `py -3 verify_066s_live_075.py --bcs "C:\Games\BG_EET_FOXX_NEW\override\BDDEFAI.BCS"` на ПК и прислал скриншот консоли. **Получено**:

- status `READ_ONLY_066S_STRUCTURE_CONFIRMED`;
- live BCS SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`;
- original 064 recovered SHA256 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`;
- 066S 1088 BCS blocks, 11 inserted, restored old 1077 blocks, `legacy_relative_order_byte_exact=true`;
- marker-bearing blocks: EPS attack 60, EPS heal 11, F guard 37.

**Interpretation**: user game has EXACT pinned 066S BCS; 064 content retained, markers EPS + F remain. This is genuine *live filesystem verification*, NOT proof of EPS runtime queue arbitration, spell timing or NPC combat reaction. **Do not suggest reinstall or rollback 066S.** No new installation performed.

## BGXAI 076 completed automatically after positive result

- New strictly read-only positional analyzer `audit_priority_076.py`, uses pinned 075 verified parser; emits ordered 1-based marker block indices and ranges from **actual local 066S BCS** without copying the script. Strict SHA gate, no game writes, `BLOCKED_NO_GAME_CHANGE` if changed.
- Source-known 066S layout: previous 061 guard receiver blocks **1032–1051**, 066S request cleanup **1052–1055**, reactive heal **1056–1061**, mage ward **1062**. Distinguish **source-known positioning** from actual EPS marker indexes (to be measured by running 076 on user PC). Historical 041 shows EPS attack/heal markers relatively early, but not proof of current live EPS priority.
- 075 receiver BAF has `ActionListEmpty()` in heal/ward rules; plausible wait for queue to empty, not demonstrated cause of observed delay. 066S frontline allowlist 2/6/12 excludes cleric; a cleric with F-on can still heal via 066S/EPS and isn't an active front-line guard in 066S. Do not assume class-only expansion is safe for dual/multi.
- Tests: `python -m unittest -q test_076.py` **19/19 PASS** on synthetic 066S + real historical 041 rejection; 4/4 SHA manifest PASS; static forbidden write/engine markers PASS. Native actual 066S BCS was not uploaded or processed by assistant; screenshot verified only 075. 076 is **SOURCE ONLY** and has **not been run on user Windows**.
- Source zip SHA256 `4f6a7c125031645d834de88f76bd088093f7e37d42d528055f87feeaac6ae6c7`; files: `verify_066s_live_075.py` (same SHA as last approved), `audit_priority_076.py`, `test_076.py`, README, manifest.

## Current state / next action

- Installed game still **066S**, 067 HOLD, 068–076 are not installed. EPS-first, preserve working F toggle, healing, spells, bard songs, manual orders.
- New read-only 076 run optional for precise marker ordering, single `py -3 .\audit_priority_076.py --bcs "C:\Games\BG_EET_FOXX_NEW\override\BDDEFAI.BCS"` after obtaining verified source. Don't ask for old archives or repeat battles. Report has no game file bytes.
- After precise positional map, develop minimal, EPS-safe corrective candidate with opt-in behavior and guarded install **only after explicit approval**; no claims of solved runtime behavior on synthetic tests.
