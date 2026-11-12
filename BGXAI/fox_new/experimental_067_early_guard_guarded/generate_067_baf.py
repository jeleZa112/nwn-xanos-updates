"""Generate 8 read-only BAF blocks: cleanup + 6 bounded prehit responses."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'BGX67_EARLY_GUARD.baf'
def generate():
 lines=['// BGXAI 067: source only, short bounded defense on verified enemy action start.',
  '// No autonomous precombat enemy search; F enabled, idle and visible threat.',
  'IF','  InParty(Myself)','  GlobalGT("BGX67_EARLY_SLOT","LOCALS",0)',
  '  !GlobalTimerNotExpired("BGX67_EARLY_EXPIRE","LOCALS")',
  'THEN','  RESPONSE #100','    SetGlobal("BGX67_EARLY_SLOT","LOCALS",0)',
  '    Continue()','END','',
  'IF','  InParty(Myself)','  GlobalGT("BGX67_EARLY_SLOT","LOCALS",0)',
  '  Global("BGX38_GUARD","LOCALS",0)',
  'THEN','  RESPONSE #100','    SetGlobal("BGX67_EARLY_SLOT","LOCALS",0)',
  '    Continue()','END','']
 for n in range(1,7):
  lines.extend([f'// P{n}: attack enemy nearest to threatened ally, then re-evaluate after 30 ticks.',
   'IF','  InParty(Myself)','  !InPartySlot(Myself,0)',
   '  Global("BGX38_GUARD","LOCALS",1)',
   f'  Global("BGX67_EARLY_SLOT","LOCALS",{n})',
   '  GlobalTimerNotExpired("BGX67_EARLY_EXPIRE","LOCALS")',
   '  !GlobalTimerNotExpired("BGX67_EARLY_COOLDOWN","LOCALS")',
   '  ActionListEmpty()', '  ModalState(NONE)',
   f'  InParty(Player{n})',f'  InPartySlot(Player{n},{n-1})',
   f'  InMyArea(Player{n})',f'  See(Player{n})',f'  Range(Player{n},30)',
   f'  See(NearestEnemyOf(Player{n}))',f'  Range(NearestEnemyOf(Player{n}),15)',
   'THEN','  RESPONSE #100',
   '    SetGlobal("BGX67_EARLY_SLOT","LOCALS",0)',
   '    SetGlobalTimer("BGX67_EARLY_COOLDOWN","LOCALS",4)',
   f'    AttackReevaluate(NearestEnemyOf(Player{n}),30)',
   'END',''])
 return '\n'.join(lines).rstrip()+'\n'
if __name__=='__main__':
 s=generate();OUT.open('w',encoding='utf-8',newline='\n').write(s);print('BAF blocks',s.count('\nIF\n'), 'bytes',len(s.encode()))
