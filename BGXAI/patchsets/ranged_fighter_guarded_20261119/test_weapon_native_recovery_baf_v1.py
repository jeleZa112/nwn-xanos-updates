#!/usr/bin/env python3
"""Source-only guard contract for existing 4-slot consumer + native emergency paths.
No installed IDS, native WeiDU or live manual/EPS origin can be certified here.
"""
from pathlib import Path
import hashlib
import re

ROOT=Path(__file__).resolve().parent
RAW=(ROOT/'BGXAI_WEAPON_SLOT_CONSUMER_V3.baf').read_text(encoding='utf-8')
ORIGINAL_SHA='f95086c3bb629aa482a8f99443fee577176b2612393be7ffac0f530c2898bf18'  # corrected by generator below
PREFIX=RAW.split('// SOURCE-ONLY NATIVE INEFFECTIVE-WEAPON RECOVERY EXTENSION',1)[0].rstrip('\n')+'\n'
blocks=re.findall(r'(?m)^IF\n(.*?)^END\s*$',RAW,re.S|re.M)
assert len(blocks)==8,len(blocks)
# Make sure the prior 4 branches were not rewritten or re-ordered.
assert hashlib.sha256(PREFIX.encode()).hexdigest()==ORIGINAL_SHA
for i,block in enumerate(blocks):
    req=i+1
    slot=i%4
    assert f'Global("BGXW3_REQ","LOCALS",{req})' in block
    assert f'HasItemSlot(Myself,SLOT_WEAPON{slot})' in block
    assert f'SelectWeaponAbility(SLOT_WEAPON{slot},0)' in block
    assert block.count('SelectWeaponAbility(')==1
    for guard in ('InParty(Myself)','!InPartySlot(Myself,0)','Global("BGX38_GUARD","LOCALS",1)',
                  'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                  'GlobalTimerNotExpired("BGXW3_LEASE","LOCALS")',
                  'ActionListEmpty()', 'ModalState(NONE)','!StateCheck(Myself,STATE_PANIC)',
                  '!StateCheck(Myself,STATE_HELPLESS)','See(NearestEnemyOf(Myself))',
                  '!InParty(NearestEnemyOf(Myself))',
                  '!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)'):
        assert guard in block,(i,guard)
    if i<4:
        assert 'WeaponCanDamage(' not in block
        assert 'BGXW3_NATIVE_PROVENANCE' not in block
    else:
        assert block.count('!WeaponCanDamage(NearestEnemyOf(Myself),MAINHAND)')==1
        assert block.count('Global("BGXW3_NATIVE_PROVENANCE","LOCALS",1)')==1
        assert block.count('SetGlobal("BGXW3_NATIVE_PROVENANCE","LOCALS",0)')==1
    assert block.count('SetGlobal("BGXW3_REQ","LOCALS",0)')==1
    assert 'Attack(' not in block and 'ClearActions(' not in block
    assert 'EquipMostDamagingMelee(' not in block and 'EquipRanged(' not in block
assert 'NOT COMPILED FOR THE USER' in RAW
assert 'explicit typed install consent' in RAW
print('PASS BAF NATIVE RECOVERY 8/8 SOURCE-ONLY GUARD BLOCKS; NO GAME DEPLOY')