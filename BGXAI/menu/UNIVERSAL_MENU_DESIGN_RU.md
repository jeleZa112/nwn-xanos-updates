# BGXAI universal class- and capability-driven menu — v0.2 SHADOW
Date: 2026-11-03. Scope: EET 2.6.6.0, SCS 35.21, EEex 1.1.7 / lefreut UI. Status: **design + tested JS configuration engine, not yet an installed game menu**.

## Never bind logic to companion names
No Imoen, Montaron, Xzar, portrait positions or hard-coded number of NPCs in runtime. Selected actor has a persistent per-campaign key provided by a verified game identity adapter, not by visual portrait order. Arbitrary number of character profiles can be stored (only current party's 1–6 is active in combat). When replacing/recruiting a companion, saved profile stays with its actor. Need to prove uniqueness and stability of key across save/load, F9, leaving/rejoining and NPC templates; don't reuse ephemeral sprite pointer without remapping.

## Two-stage class architecture
**Stage 1: capabilities.** EEex adapter reads active classes/levels, kit, special abilities, current thieving skills, equipped permitted weapons, prepared spells, song, dual-class suspension, status effects, nearby visible enemies and orders. Map to verified true/false/unknown features: martial, melee, ranged, thief, detectTraps, disarmTraps, pickLocks, stealth, arcane, divine, heal, summon, buff, song, sneakAttack. *Active dual* abilities must be turned off when inactive; forbidden schools and exhausted spell slots must not be inferred merely from class name.

**Stage 2: user role and permissions.** Auto role suggestions vs manual role: tank, ranged, scout, controller, healer, striker, hybrid. Menu toggles: ranged/melee, scan, disarm, open, hide, sneak attack, arcane offence/defence, divine offence, heal, buffs, summons, songs, retreat. Shared party mode travel/combat/boss/stealth/rest + per-actor stance cautious/balanced/aggressive/manual. A mode modifies permissions temporarily, never rewrites individual profiles. Disabled entries visibly explain absent skill/class spell.

## Safety requirements
1. Manual controls and busy actions override AI. Never hijack a cast or chase a locked object.
2. `PickLock(object)` and `RemoveTraps(trap)` gated on **a specific visible, reachable, pre-checked and explicitly player-approved target** with quest sensitivity denied. No silent chest theft/pickpocket.
3. No trap re-pathfinding without confirmed safe route. No 3E sneak attack on ranged attacks. A hidden character's stealth never broken for auto melee attack until path safety proven.
4. For available spells, class flag alone insufficient: use real prepared spell slots, range, target, kit restrictions, immunities; fallback to weapon. `verifiedFeatures` defaults unknown to disabled, not enabled.
5. Campaign names and personal secrets must not appear in public telemetry. Object IDs local; upload anonymized incidents only.
6. Safe UI integration as EEex additional menu/lua, avoid editing lefreut UI.MENU / SCS menu directly. EEex LoadMenuFile and reset listener from documented APIs still require live testing in this exact installation.

## Files and tests
- `BGXAI/menu/BGX_MENU_UNIVERSAL_V02.js`: tested pure JS profiles + capability permissions engine (no hooks).
- **32/32 isolated tests passed**: arbitrary identities, respec detection, dual inactive flags, class/kit gates, per-object lock permission, role selection, manual priority, group modes, safe serialization.
- Actual GUI `BGX_MENU.MENU` and bridge `M_BGXMENU.lua` **not yet implemented or installed**. Active `BGXAI/latest.json` remains 0.6.27 role pilot; this config engine is NOT connected to its BAF executors. No promises of automatic, fully functional game menu yet.
