# BGXAI 078 — EPS-FIRST SMART HEAL SELECTOR, SOURCE ONLY — 2026-11-14

User complained correctly that work was being stopped after completed source-only steps in violation of global auto-continue rule. Immediately progressed to substantive next step without asking for repeated confirmation.

**Game:** Actual installed 066S was confirmed by user 075 + 076R1 on the real game; live BCS 1088 blocks, SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`, preserved EPS healing/attack and F guard. 067 HOLD. 068–078 SOURCE ONLY. Nothing installed/edited on the user PC, and no changes to updater/WeiDU/M_BX43.lua/BDDEFAI.BCS.

**077 input proof:** original BGX61_RECEIVER.baf, BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf, BGX66_CASTER_SUPPORT.lua, M_BX43_066S_CASTER_CANDIDATE.lua were SHA rechecked. 077 revealed closest-only healer selection with late BCS spell/range/queue checks; 18 061 guard and 7 066S caster action blocks have `ActionListEmpty`. No direct overlap between guard 2/6/12 and healer 3/8/11/14/15/16/17/18 in current 066S Lua, though EPS may act separately.

**078 built:** `BGXAI078_HEAL_SELECTOR.lua` pure, opt-in default OFF. Systematically scans candidate snapshots and rejects missing actual CLW spell, invalid range 10, busy EPS queue, existing heal, manual/casting/song/trap, inactive F, dead or unknown actors; chooses nearest *available* and falls back to next candidate, tie-break by portrait slot. Shaman, multiclass, dual only eligible upon verified actual ability. No raw CLASS.IDS hardcoding, no EEex hooks or Lua game writes. All engine action output false, status advisory only. Cannot claim live in-game auto-healing until EEex fact provider is proven and a separately approved patch installed.

**Tests:** 88 native texlua assertions PASS, 14 Python unittest PASS (private-source integrity and source no-write); release SHA manifest verified, source-only. Exact test counts are of model/fixtures, not engine runtime.

**Files:** Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_078_EPS_FIRST_HEAL_SELECTOR_SOURCE_ONLY/`, Library checkpoint `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_078_CHECKPOINT_20261114_RU.md`, GitHub branch `bg-eet-ai` `BGXAI/fox_new/experimental_078_eps_first_heal_selector_source_only/` and `BGXAI/CURRENT/BGXAI_078_CHECKPOINT_20261114_RU.md`.

**Next safe task:** read-only EEex verified fact adapter for current prepared spell + Range + queue without modifying live game, then integration tests and guarded opt-in. Continue automatically when possible; do not promise asynchronous work.
