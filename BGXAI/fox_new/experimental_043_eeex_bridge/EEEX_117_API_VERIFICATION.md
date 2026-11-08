# EEex 1.1.7 API evidence for BGXAI 043

Pinned upstream tag: https://github.com/Bubb13/EEex/releases/tag/v1.1.7 (`cd016e03d7c62968d8ab917f44eef09bef25593a`).

Verified directly in upstream source `EEex/copy/EEex_scripts/EEex_Action.lua`:
- `function EEex_Action_AddSpriteStartedActionListener(func)` stores the listener in a table.
- `function EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)` iterates that table and invokes `EEex_Utility_TryIgnore(listener,sprite,action)` where `action=sprite.m_curAction`.
- Current action fields used by upstream: `m_actionID`, `m_acteeID.m_Instance`.

Verified in `EEex/copy/EEex_scripts/EEex_Sprite.lua`:
- `function EEex_Sprite_GetInPortraitID(portraitIndex)` accesses `...m_charactersPortrait:get(portraitIndex)`, indices [0-5].
- `sprite.m_id` and modal-related object API used in upstream.

Verified in `EEex/copy/EEex_scripts/EEex_Action.lua` and `EEex_GameObject.lua`: `sprite.m_pos.x/y` and `object.m_pos.x/y` are valid field paths in upstream examples/implementations.

The started-action callback does **NOT** expose an action-source flag. It is unsound to derive a manual-vs-script command solely from action opcode. Hence execution remains disabled even if action 3/105 originates from another sprite targeting a party member.

No claim of live runtime testing in user's specific EET. No bundled upstream code; source references only.
