#!/usr/bin/env python3
"""Emit BGXAI 060's bounded trigger-gated BCS response; NO installation.

The existing 056 Lua writes one verified weapon-hit request to the guardian's
LOCALS. This replaces 056's 8 receiver blocks, NOT EPS / magic / UI.
"""
from pathlib import Path

COMMON = '''  InParty(Myself)
  !InPartySlot(Myself,0)
  Global("BGX38_GUARD","LOCALS",1)
  Global("BGX52_REQ_SLOT","LOCALS",{slot})
  GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")
  !GlobalTimerNotExpired("BGX52_COOLDOWN","LOCALS")
  ActionListEmpty()
  ModalState(NONE)
  InParty(Player{slot})
  InPartySlot(Player{slot},{portrait})
  !InPartySlot(Myself,{portrait})
  See(Player{slot})
  Range(Player{slot},10)
'''

CLEANUPS = '''// 060: expire a stale confirmed-hit advisory and honor F=OFF.
IF
  InParty(Myself)
  GlobalGT("BGX52_REQ_SLOT","LOCALS",0)
  !GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    Continue()
END

IF
  InParty(Myself)
  GlobalGT("BGX52_REQ_SLOT","LOCALS",0)
  Global("BGX38_GUARD","LOCALS",0)
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    Continue()
END
'''


def generate():
    blocks = [CLEANUPS]
    for slot in range(1, 7):
        shared = COMMON.format(slot=slot, portrait=slot-1)
        # Prioritize the actual attacker of the damaged party member.
        # Old 056 required See(NearestEnemyOf(PlayerN)), which can be a different
        # hostile or none at all. The actual attacker is the actionable target.
        blocks.append(f'''// P{slot} direct retaliation, only after EEex-confirmed hit and if guardian idle.
IF
{shared}  See(LastAttackerOf(Player{slot}))
  Range(LastAttackerOf(Player{slot}),10)
  !InParty(LastAttackerOf(Player{slot}))
  !Allegiance(LastAttackerOf(Player{slot}),GOODCUTOFF)
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    SetGlobalTimer("BGX52_COOLDOWN","LOCALS",4)
    SetGlobal("BGX60_LAST_BRANCH","LOCALS",1)
    SetGlobal("BGX60_LAST_VICTIM","LOCALS",{slot})
    AttackReevaluate(LastAttackerOf(Player{slot}),30)
END
''')
    for slot in range(1,7):
        shared=COMMON.format(slot=slot,portrait=slot-1)
        # If attacker cannot be seen/identified, attempt existing native guard
        # behavior without requiring NearestEnemyOf(victim) to be visible.
        blocks.append(f'''// P{slot} fallback: protect hit victim without a speculative enemy selector.
IF
{shared}THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    SetGlobalTimer("BGX52_COOLDOWN","LOCALS",4)
    SetGlobal("BGX60_LAST_BRANCH","LOCALS",2)
    SetGlobal("BGX60_LAST_VICTIM","LOCALS",{slot})
    ProtectObject(Player{slot},6)
END
''')
    return '// BGXAI 060 TEST CANDIDATE - READ AND COMPILE BEFORE ANY GAME INSTALL\n// 056 Lua remains unchanged; no global player order, ClearActions or spells.\n\n'+ '\n'.join(blocks)

if __name__=='__main__':
    p=Path(__file__).with_name('BGX60_RECEIVER.baf')
    p.write_text(generate(),encoding='ascii',newline='\n')
    print(p.name, len(generate()), 'characters')
