# BGXAI 073 — cross-module safety, 2026-11-14

User insists on mandatory auto-continue after successful safe offline work, no waiting for additional approval for source-only stages. BGXAI 071 and 072 were completed and verified in this turn; 073 developed as next safe step. No background work claimed.

**GAME STATE:** EET Foxx 05.11.2026, SCS 35.21, EPS 18.4, EEex 1.1.7, Insane. Installed BGXAI 066S. 067 on HOLD, 068–073 SOURCE ONLY; user has not authorized game modification. F-Guard is custom BGXAI function, NOT an EPS standard switch.

**071 revalidated:** 240 native Lua assertions, 9 Python tests, 9 SHA entries PASS. Static 15,159 CRE V1.0 audit in preserved user resource archive already completed with private raw material not republished. CRE raw shapeshifter kit=0x40110000 vs KIT.IDS token=0x4011; raw kit and level bits do not prove live character state.

**072 revalidated:** 66 native Lua assertions, SHA and passive checks PASS. EPS-first arbiter requires verified explicit attacker, exact proposed target, no pending cure/cast/song/manual action/trap detection, known empty EPS action queue. Always advisory; never dispatches game orders.

**073 new:** `BGXAI073_CROSS_MODULE_AUDIT.lua` combines 069 passive role, 070 EEex snapshot, 071 kit hint, 072 arbiter. `test_073.lua` **142/142 assertions PASS** on synthetic EEex inputs incl fighter/cleric/fighter-druid/shapeshifter/shaman, locked dual uncertainty, F off, HP low, malformed kit raw. It proves only safety invariants in a simulated workflow: no raw KIT/CRE hint promoted to verified live kit; polymorph flag not promoted to verified werewolf; levels do not prove unlocked dual; unknown EPS action state blocks guard. `verify_073.py` static forbidden-action scan and SHA256 checks PASS. ZIP SHA256 `3f51e220e25def720af29f0b0cd28a55302b04a4cbf45b3acf422a5d51220281`.

**No modifications** to `M_BX43.lua`, `BDDEFAI.BCS`, `WeiDU.log`, one-file updater, EPS, F hotkey or user PC. No real EEex runtime test claimed. This is not a new installed AI.

Files: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_073_CROSS_MODULE_INVARIANTS_SOURCE_ONLY/` and `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_073_CHECKPOINT_20261114_RU.md`; GitHub repo `jeleZa112/nwn-xanos-updates`, branch `bg-eet-ai`, `BGXAI/fox_new/experimental_073_cross_module_invariants_source_only/`, `BGXAI/CURRENT/BGXAI_073_CHECKPOINT_20261114_RU.md`.

**Next safe work:** inspect authentic EPS/BCS action queue mechanics and EEex available function names from user-preserved source data. No automatic live install until verified actual kit/dual/form, EPS action arbitration, exact targeting, and guarded Windows preflight. User need not resend old resource archives.
