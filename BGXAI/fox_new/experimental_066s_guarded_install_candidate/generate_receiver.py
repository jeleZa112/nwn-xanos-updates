"""Deterministic guarded 066S BAF receiver source, NOT inserted into active BCS.
Real WeiDU compile against the user's current BCS/IDS is required before install.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'
head='''// BGXAI 066S - SOURCE ONLY BCS caster support. NOT INSTALLED.
// Injection point (only after proven WeiDU merge): after existing F toggle,
// before legacy 042B/EPS blocks. Existing 064 receiver retained byte-exact.
// Cleanup expired/F-OFF requests. Never force manual action interruption.
IF
  InParty(Myself)
  GlobalGT("BGX66_S_HEAL_SLOT","LOCALS",0)
  !GlobalTimerNotExpired("BGX66_S_HEAL_EXPIRE","LOCALS")
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_HEAL_SLOT","LOCALS",0)
    Continue()
END

IF
  InParty(Myself)
  GlobalGT("BGX66_S_HEAL_SLOT","LOCALS",0)
  Global("BGX38_GUARD","LOCALS",0)
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_HEAL_SLOT","LOCALS",0)
    Continue()
END

IF
  InParty(Myself)
  Global("BGX66_S_WARD","LOCALS",1)
  !GlobalTimerNotExpired("BGX66_S_WARD_EXPIRE","LOCALS")
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_WARD","LOCALS",0)
    Continue()
END

IF
  InParty(Myself)
  Global("BGX66_S_WARD","LOCALS",1)
  Global("BGX38_GUARD","LOCALS",0)
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_WARD","LOCALS",0)
    Continue()
END

'''
parts=[head]
for i in range(1,7):
    obj=f'Player{i}'
    n=i-1
    parts.append(f'''// Cleric/druid support. The engine checks actual memorisation and injured target.
IF
  InParty(Myself)
  !InPartySlot(Myself,0)
  Global("BGX38_GUARD","LOCALS",1)
  Global("BGX66_S_HEAL_SLOT","LOCALS",{i})
  GlobalTimerNotExpired("BGX66_S_HEAL_EXPIRE","LOCALS")
  !GlobalTimerNotExpired("BGX66_S_HEAL_COOLDOWN","LOCALS")
  ActionListEmpty()
  ModalState(NONE)
  HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)
  InParty({obj})
  InPartySlot({obj},{n})
  HPPercentLT({obj},45)
  See({obj})
  Range({obj},10)
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_HEAL_SLOT","LOCALS",0)
    SetGlobalTimer("BGX66_S_HEAL_COOLDOWN","LOCALS",12)
    Spell({obj},CLERIC_CURE_LIGHT_WOUNDS)
END

''')
parts.append('''// Emergency mage self-defense only after confirmed hit on THIS mage.
// Single low-level spell, one request, long cooldown; no pre-hit guessing.
IF
  InParty(Myself)
  !InPartySlot(Myself,0)
  Global("BGX38_GUARD","LOCALS",1)
  Global("BGX66_S_WARD","LOCALS",1)
  GlobalTimerNotExpired("BGX66_S_WARD_EXPIRE","LOCALS")
  !GlobalTimerNotExpired("BGX66_S_WARD_COOLDOWN","LOCALS")
  ActionListEmpty()
  ModalState(NONE)
  HPPercentLT(Myself,26)
  HaveSpell(WIZARD_SHIELD)
  See(NearestEnemyOf(Myself))
THEN
  RESPONSE #100
    SetGlobal("BGX66_S_WARD","LOCALS",0)
    SetGlobalTimer("BGX66_S_WARD_COOLDOWN","LOCALS",9000)
    Spell(Myself,WIZARD_SHIELD)
END
''')
OUT.write_text(''.join(parts),encoding='utf-8',newline='\n')
print('066S BAF blocks:',OUT.read_text().count('IF\n'),'bytes',OUT.stat().st_size)