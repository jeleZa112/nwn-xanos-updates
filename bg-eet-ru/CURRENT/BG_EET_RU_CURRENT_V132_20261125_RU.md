# BG_EET_RU — CURRENT V132, 25.11.2026

## Latest real gameplay evidence
Installed V126 passive UI.MENU observer was verified: 72 actual printed combatLog rows, 11 d20 results (5 HIT, 6 MISS) from SEND_TO_CHATGPT_BG_EET_RU(20261124-164826).zip. No game modifications during capture, no native to visible row join. Never rerun this already completed battle or 14 legacy stages.
V129 actual game Hit() code demonstrates that AddMessage callsite at 0x39E84B is conditional, so missing message != MISS. V131 actual game PE report from SEND_TO_CHATGPT_BG_EET_RU(20261124-171543).zip: EXE SHA fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580; function 0x39DA50-0x39E9DC; SizeOfProlog 31; candidate 0x39DA6F starts exactly after prologue, no installed new native hook. V131 JSON lost raw extra UNWIND_CODE operand values (only extra_slots count); this is resolved by V132 reader once user runs it.

## New upstream EEex finding
Official source Bubb13/EEex at EEex/copy/EEex_scripts/EEex_Assembly_x86-64.lua (Git blob e8c6a2fe303fdac3e92d9df9ea25c6a7af1e5a5c) includes function EEex_Assembly_Private_WriteAndRegisterFunctionTable / PostJIT, EEex_RtlLookupFunctionEntry and EEex_RtlAddFunctionTable, as well as EEex_HookBeforeRestoreWithLabels and EEex_HookCallInternal with JITNear/JITAt. Thus public upstream has x64 JIT unwind registration support, but installed version/hash and runtime owner are NOT verified.

## V132 merged implementation
Source: bg-eet-ru/native-correlation/v132_eeex_unwind_contract_ro.py, immutable commit 1607cfc1426dcd01621fae8dea5648115f37e7c3, SHA256 6dfaf835b7d84a25f25eb55e96fd91a0d4f15d62329ceb57c2337027156166be.
Read-only: exact Baldur.exe SHA; raw UWOP_SAVE_NONVOL RBX operand 27*8=216 alongside ALLOC128 and 7 pushes; installed EEex_scripts/EEex_Assembly_x86-64.lua file SHA and JIT/unwind helper symbols; EEex_Sprite_Patch file SHA; InfinityLoader.db FirstCall label presence. It does NOT claim source-present = loaded, or JIT owner, ABI/XMM, runtime unwind, rollback, gameplay, or correct weapon on misses.
One published user updater: bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd, SELF_VERSION 132, 749856 bytes, SHA256 b4b6d8dd864dc2ad6beeec50965015396e8d5f02efc22c0071dc8f5835e86644. release.json has version 132 and matching sha. ONE new menu option 7=abi, which adds 65_V132_EEEX_ABI.json to existing SEND_TO_CHATGPT_BG_EET_RU.zip; old 6=unwind preserved. No game file writes.
PR #103 merged squash commit 1b2e286a08ea1565b6b497e8b863ebaa25d9d7cd. Windows+Linux CI PASS run 45449008377 including new V132 source download/cache and fake-game regression, previous V131 onefile, 14 stages, real Lua and full selftest. PR #102 draft closed.

## Next (one user action only)
Run EXISTING C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd, let update to V132, choose 7=abi, then upload ONE SEND_TO_CHATGPT_BG_EET_RU.zip. Don't choose 1 (14 previous checks), 2 (UI install), 4 (battle), 6 (V131 already completed). Don't reinstall/remove V126. On failure/HOLD preserve game and send ZIP.
Examine only 65_V132_EEEX_ABI.json to establish actual installed EEex Lua source and saved RBX raw unwind operand. Then engineer hook owner, ABI/XMM, exception-safety, safe rollback, and event->UI-row join, with separate explicit typed install approval. Do not pretend source-only PASS means gameplay PASS.

Other projects (BGXAI and BG Voice RU), game EXE, TLK, saves and existing V108 / V126 must remain unchanged. Current game-changing native hook install authorization: NONE.