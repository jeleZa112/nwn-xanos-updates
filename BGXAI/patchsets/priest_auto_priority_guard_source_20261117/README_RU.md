# BGXP5 — AUTO priority heal + protection against attacking party members

17.11.2026. Designed for the **installed BGXP3** in EET Foxx (5 Nov 2026). Must only be installed after **real EET native WeiDU preflight** and explicit consent in the existing one-file updater.

## What actually failed

In BGXP3, user's second companion was critically injured (3/14 HP, ~21%), Jagan remained 8/8 HP and AUTO did not heal. Earlier, at Jade 2/6 HP, AUTO also failed to heal. Command and attack were successful after approaching the enemy. User also reported AI assisting attacks against an ally; screenshot alone doesn't show Jagan's target, so treat as an urgent friendly-targeting safety concern, not a conclusively confirmed engine event.

Source inspection found BGXPR AUTO's six Cure Light Wounds actions **late** in the 1158-block script, and gated by `ActionListEmpty`, seeing the ally and Range 10. Existing companion-approach actions are also gated by enemy-distance checks. BGXP3 only raised the prohibition on starting a new AUTO attack to below 60% HP, **not actual healing priority**.

## The new source-level behavior

- **12 new high-priority blocks** prepended **before EPS** in the same BCS: for party slots 1–6, first for HP below 35%, then for HP below 70%, guarded by AUTO role 4, Guard F ON, `ActionListEmpty()`, memorized `CLERIC_CURE_LIGHT_WOUNDS`, cooldown, party/slot/in-area, visibility and a bounded **Range 18**.
- Uses the existing memorized spell with ordinary `Spell(PlayerN,CLERIC_CURE_LIGHT_WOUNDS)`. Does not use unmemorized casts, ForceSpell, ClearActions, ActionOverride or bypass user commands. Even at Range 18, the target may need to be approached for the *touch-range* cure; real game test is required.
- All **four BGXP3 combat blocks** (BATTLE/AUTO Command and AttackOneRound) explicitly require `!InParty(NearestEnemyOf(Myself))` in addition to their existing enemy visibility/range gates. Prevents **our new combat blocks** attacking members of the same party, including if the engine temporarily treats an ally as hostile. Does not prevent older EPS blocks or manual orders from targeting allies.
- Last BGXP3 AUTO AttackOneRound's **60% protection remains**.
- Retains all 1158 existing blocks in order except the four specified combat blocks; **1154 old blocks byte-for-byte unchanged**, 12 new heal blocks at top; resulting 1170 blocks. Lua and all BG_EET_RU/BG Voice RU files untouched.

## Strict release and installation behavior

- Baseline BCS SHA256 `c63173381aa93de799b02ab203337c2444c0b50a7268a95130a768e5d0ca28e3`, Lua SHA256 `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`. Last WeiDU **BGXP3**. `BGXP3/STAGED_PROOF.json` must match.
- `BGXP5_BCS_PREFLIGHT_READ_ONLY.py` compiles three BAF resources using real EET IDS and the game's WeiDU in temporary directories. Asserts the original BGXP3 compiled 28-block tail equals live BCS; the guarded tail only changes the last four; the twelve new cure blocks have exactly timer+memorized spell actions.
- `BGXP5_INSTALL.py` only installs after the above checks, rechecking baseline and source SHAs and generating an external SHA-verified snapshot at `Documents\BGXAI_PRIEST5_SAFE_BACKUPS\PRE_INSTALL_...\`. Native compiled candidate determinism is required.
- Uses WeiDU component **BGXP5** and exact typed opt-in `INSTALL_BGXP5_EARLY_HEAL_SAFE`; guarded rollback `ROLLBACK_BGXP5_EARLY_HEAL_SAFE` only when BGXP5 last. Never retry a failed install automatically.

## Important limitations

**This is a new priority candidate, not a proven in-game cure.** If Jagan is busy executing a manual action or persistent EPS attack, `ActionListEmpty` stays false and the BCS still will not interrupt it. Visibility, range, memorized slots, silence/panic or heal reservation may also prevent action. Jagan will not necessarily *run across the room*. If the real preflight fails, leave the installed BGXP3 untouched and examine the exact error. Do not claim success until the next game playtest.

The existing auto-updater is the only supported installation method. Do not run the installer directly or update the game without separate typed authorization and verification.
