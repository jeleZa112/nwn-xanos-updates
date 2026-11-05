#!/usr/bin/env python3
"""Read-only regression gate for the USER's EET ordinary Advanced AI.
Requires their own BG_EET_AUDIT_02_QUESTS_AI.zip; no copyrighted BCS bundled.
This is static structural evidence, not a substitute for actual game testing.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json
import re
import sys

SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/BGXAI_REBUILD020_sources/BG_EET_AUDIT_02_QUESTS_AI.zip')
ACTIONS={296:'BattleSong',3:'Attack',105:'AttackOneRound',134:'AttackReevaluate',355:'RunAwayFromNoLeaveArea',31:'Spell',36:'Continue'}
PAT=re.compile(r'(?m)^AC\n(\d+)OB\n')
with ZipFile(SOURCE) as z:
    names=['BDDEFAI.BCS','BDBARD01.BCS','BDBARD20.BCS','BDFTHI01.BCS']
    stats={}
    for name in names:
        b=z.read(name)
        s=b.decode('latin1')
        act=Counter(map(int,PAT.findall(s)))
        stats[name]={
            'size':len(b),'sha256':sha256(b).hexdigest(),
            'action_names':{label:act.get(a,0) for a,label in ACTIONS.items()},
            'locals_bard_mode':('LOCALSBDAI_SKILL_MODE' in s),
            'locals_bard_state':('LOCALSBD_BRDS' in s),
            'controls_no_retreat':('localsbd_no_retreat' in s.lower()),
        }
    stock=z.read('BDDEFAI.BCS').decode('latin1')
    pos=stock.index('AC\n296OB\n')
    block_start=stock.rfind('CR\n',0,pos)
    block_end=stock.find('CR\n',pos+3)
    bard_block=stock[block_start:block_end]
    checks={
        'stock_BDDEFAI_contains_BattleSong_action296': 'AC\n296OB\n' in stock,
        'bard_song_block_uses_BDAI_SKILL_MODE': 'LOCALSBDAI_SKILL_MODE' in bard_block,
        'bard_song_block_updates_BD_BRDS': 'LOCALSBD_BRDS' in bard_block,
        'bard_class_script_present':'BDBARD01.BCS' in z.namelist(),
        'bard_alt_class_script_present':'BDBARD20.BCS' in z.namelist(),
    }
    assert all(checks.values()), checks
    report={'status':'PASS: static stock bard invariants only',
      'source':str(SOURCE.name),'game_files_modified':False,
      'stock':stats,'checks':checks,
      'scs_v35_21_external_source':{
          'repo':'Gibberlings3/SwordCoastStratagems',
          'tag':'v35.21',
          'file':'stratagems/gameplay/resource/bddefai.ssl',
          'verified_from_github_connector':True,
          'verified_sha1_blob':'fe8bca172924aad2604ec889de1ceec4f40a5647',
          'observed_contains_BattleSong':False,
          'observed_contains_AttackReevaluate':False,
          'observed_contains_Attack':True,
          'observed_contains_WeaponCanDamage':True,
          'observed_contains_WeaponEffectiveVs':True,
      },
      'limitations':['Not a runtime bard song/casting continuity proof','No user current save slot assignment verified','Historical SCS 5000 in old WeiDU log does not mean present now','Do not replace live BGXUN1 until explicit verified beta']}
print(json.dumps(report,ensure_ascii=False,indent=2))