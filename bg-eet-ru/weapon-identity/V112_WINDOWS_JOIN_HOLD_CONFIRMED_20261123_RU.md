# BG_EET_RU — V112 Windows JOIN_HOLD confirmed (2026-11-23)

## Verified new Windows ZIP (private, not published)
Upload `SEND_TO_CHATGPT_BG_EET_RU(20261123-150617).zip`: **809870 bytes**, SHA256 `6b7d80d36484b1f4d002b11d4d160cece5bb38c375187d32a5be2e73f61efdc4`; **127 unique files, CRC PASS**. One new report: `56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json`.

V112 report:
- `updater_version=112`, `status=V112_ITEM_NAMES_AND_UI_SOURCE_CONFIRMED_JOIN_HOLD`, `errors=[]`, `game_files_written=0`, `new_hook_installed=false`.
- `override/UI.MENU` source scan found `combatLog[rowNumber]`, `BG_EET_RU_LogView`, `BG_EET_RU_LOG_MODE`, `WORLD_MESSAGES`.
- `EEex_scripts/EEex_Action.lua` source scan found `EEex_Action_AddSpriteStartedActionListener`, `EEex_Action_Private_SpriteStartedActionListeners`.
- History from same ZIP retains V108 **two live damage callbacks** `weapon_resref=AROW01` / `launcher_resref=BOW05`; both lack `attacker_id`, `target_id`, `attack_sequence`, and `journal_row_id`. Old V106 logged `attacker:userdata`, `target:userdata`, but not stable identifiers or direct row association.
- V111 all three installed RU names still resolved: sword `SW1H04` identified “Длинный меч”, `AROW01` identified “Стрела” (unidentified name is **“Отличная стрела”**), `BOW05` identified “Короткий лук”.

## Upstream source-only research
Official EEex (commit `a6d21abe44e20509f5d0259ccc6c7e7f9d12b285`):
- `EEex_Action.lua` implementation `EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)` obtains `sprite.m_curAction` and notifies started-action listeners with `(sprite, action)`. **Not** a promised callback for each attack roll, hit or miss and **no combatLog row ID**: https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Action.lua
- `EEex_Action_Patch.lua` calls that function after `CGameSprite::SetCurrAction()`, not after every weapon swing: https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Action_Patch.lua
- `EEex_Sprite_Patch.lua` uses damage path `CGameSprite::Override_Damage` and native roll storage `CGameSprite_Hit_Roll`, but no documented safe observer for each miss and row ID proven: https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite_Patch.lua

**Conclusion:** PRESERVE `JOIN_HOLD`. Do not fabricate an exact per-attack/row association via action start, last weapon, approximate time or queue order, especially with APR, dual wield, multiple attackers and projectiles in flight. Keep functioning V101 FULL/BRIEF and V108. No additional live test needed yet. A subsequent guarded **source-first** design must first show a safe, common per-roll and per-row correlation key (or an equivalently unambiguous single-origin event), including misses; if impossible preserve original log rendering rather than claim misattributed weapon.

Private JSON evidence + handoff in Library `/BG_EET_RU/CURRENT/BG_EET_RU_V112_WINDOWS_JOIN_HOLD_AUDIT_20261123.json`, `/BG_EET_RU/CURRENT/BG_EET_RU_V112_WINDOWS_JOIN_HOLD_HANDOFF_20261123.md`. One updater, one ZIP. No private user ZIP uploaded to GitHub.
