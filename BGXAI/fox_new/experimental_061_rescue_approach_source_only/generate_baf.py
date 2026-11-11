#!/usr/bin/env python3
"""BGXAI 061 - bounded approach after confirmed EEex hit. Source only."""
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
  InMyArea(Player{slot})
'''
CLEANUPS = '''// Clear expired request and F=OFF, retaining 060's original safety.
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
    blocks=[CLEANUPS]
    # 1. Immediate attack when close and actual last attacker visible.
    for slot in range(1,7):
        c=COMMON.format(slot=slot,portrait=slot-1)
        blocks.append(f'''// P{slot}: immediate retaliation after confirmed hit (0..10 feet to victim).
IF
{c}  See(Player{slot})
  Range(Player{slot},10)
  See(LastAttackerOf(Player{slot}))
  Range(LastAttackerOf(Player{slot}),10)
  !InParty(LastAttackerOf(Player{slot}))
  !Allegiance(LastAttackerOf(Player{slot}),GOODCUTOFF)
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    SetGlobalTimer("BGX52_COOLDOWN","LOCALS",4)
    SetGlobal("BGX61_LAST_BRANCH","LOCALS",1)
    SetGlobal("BGX61_LAST_VICTIM","LOCALS",{slot})
    AttackReevaluate(LastAttackerOf(Player{slot}),30)
END
''')
    # 2. An ally at 11..40 feet is a rescue target, not a failed close-range guard.
    # Do not clear Q: on arrival BCS may execute ProtectObject/attack.
    # Single movement action plus cooldown; never interrupt a cast or manually queued action.
    for slot in range(1,7):
        c=COMMON.format(slot=slot,portrait=slot-1)
        blocks.append(f'''// P{slot}: approach endangered ally after confirmed hit; same area, max 40 feet.
IF
{c}  !Range(Player{slot},10)
  Range(Player{slot},40)
THEN
  RESPONSE #100
    SetGlobalTimer("BGX52_EXPIRE","LOCALS",20)
    SetGlobalTimer("BGX52_COOLDOWN","LOCALS",2)
    SetGlobal("BGX61_LAST_BRANCH","LOCALS",3)
    SetGlobal("BGX61_LAST_VICTIM","LOCALS",{slot})
    MoveToObject(Player{slot})
END
''')
    # 3. When guardian is close, native ProtectObject without nearest enemy test.
    for slot in range(1,7):
        c=COMMON.format(slot=slot,portrait=slot-1)
        blocks.append(f'''// P{slot}: native protection of hit ally near the guardian.
IF
{c}  See(Player{slot})
  Range(Player{slot},10)
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    SetGlobalTimer("BGX52_COOLDOWN","LOCALS",4)
    SetGlobal("BGX61_LAST_BRANCH","LOCALS",2)
    SetGlobal("BGX61_LAST_VICTIM","LOCALS",{slot})
    ProtectObject(Player{slot},6)
END
''')
    return ('// BGXAI 061: candidate BCS executor, after successful 060 close-range partial behavior.\n'
            '// F=ON and verified on-hit Q required. Preserve 060 cleanup, EPS and manual actions.\n'
            '// InMyArea + 40 ft bounds approach. No autonomous precombat wandering.\n\n'
            + '\n'.join(blocks))

if __name__=='__main__':
    f=Path(__file__).with_name('BGX61_RECEIVER.baf')
    f.write_text(generate(),encoding='ascii',newline='\n')
    print(f.name, len(generate()), 'bytes')
