#!/usr/bin/env python3
"""BGXAI read-only GAM one-shot candidate evidence, not an installer or action generator.
Extracts only a snapshot-bound proposed transaction and explicit blockers.
All byte reads are bounded. Never writes to or modifies the input GAM.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path

class Hold(ValueError):
    pass

SLOTS_TO_RUNTIME=(6,1,9,5,7,8,0,2,3,35,36,37,38,11,12,13,14,4,15,16,17,*range(18,34),34)
assert len(SLOTS_TO_RUNTIME)==38 and len(set(SLOTS_TO_RUNTIME))==38


def _get(raw:bytes,start:int,size:int)->bytes:
    if start < 0 or size < 0 or start + size > len(raw):
        raise Hold('HOLD_BAD_OFFSET')
    return raw[start:start+size]

def _num(raw:bytes,off:int,fmt:str):
    return struct.unpack('<'+fmt,_get(raw,off,struct.calcsize('<'+fmt)))[0]

def _short_ascii(raw:bytes)->str:
    raw=raw.split(b'\x00',1)[0].rstrip(b' ')
    if raw and not all((65<=x<=90 or 97<=x<=122 or 48<=x<=57 or x in (35,42,95)) for x in raw):
        raise Hold('HOLD_BAD_NAME_BYTES')
    return raw.decode('ascii').upper()

def read_party(data:bytes):
    if type(data) is not bytes or not (164 <= len(data) <= 50_000_000):
        raise Hold('HOLD_INVALID_FILE_SIZE')
    if data[:8]!=b'GAMEV2.0': raise Hold('HOLD_UNSUPPORTED_GAME_VERSION')
    po,n=_num(data,0x20,'I'),_num(data,0x24,'I')
    if not 1<=n<=6: raise Hold('HOLD_PARTY_COUNT')
    _get(data,po,n*0x160)
    party=[]
    known_party_indices=set()
    for i in range(n):
        base=po+i*0x160
        index=_num(data,base+2,'H')
        if index>5 or index in known_party_indices:raise Hold('HOLD_PARTY_INDEX')
        known_party_indices.add(index)
        off,size=_num(data,base+4,'I'),_num(data,base+8,'I')
        cre=_get(data,off,size)
        if cre[:8]!=b'CRE V1.0':raise Hold('HOLD_UNSUPPORTED_CRE_VERSION')
        if len(cre)<0x2d4:raise Hold('HOLD_SHORT_CRE')
        slot_off,item_off,item_count=(_num(cre,0x2b8,'I'),_num(cre,0x2bc,'I'),_num(cre,0x2c0,'I'))
        if item_count>1000:raise Hold('HOLD_TOO_MANY_ITEMS')
        slots=_get(cre,slot_off,80)
        itemraw=_get(cre,item_off,item_count*20)
        contents={}; used=set()
        for k,runtime in enumerate(SLOTS_TO_RUNTIME):
            at=_num(slots,k*2,'H')
            if at==65535:
                contents[runtime]=None
            else:
                if at>=item_count or at in used:raise Hold('HOLD_DUPLICATE_OR_INVALID_ITEM_INDEX')
                used.add(at)
                er=_get(itemraw,at*20,20)
                contents[runtime]={'resref':_short_ascii(er[:8]),'charges':list(struct.unpack_from('<3H',er,10)),
                    'expiry':_num(er,8,'H'),'flags':_num(er,16,'I'),'creItemIndex':at}
        if len(used)!=item_count:raise Hold('HOLD_UNREFERENCED_ITEM')
        top_name=_short_ascii(_get(data,base+12,8))
        display=_get(data,base+0xc0,32).split(b'\x00',1)[0].decode('cp1252',errors='replace')
        death=_short_ascii(_get(cre,0x280,32))
        # IESDP CRE V1.0 0x248..0x268: saved CRE script assignments only.
        # These are neither proof of an executing BCS nor EEex SCRLEV 1/2.
        saved_scripts={str(level):_short_ascii(_get(cre,offset,8))
                       for level,offset in ((0,0x248),(4,0x250),(5,0x258),
                                            (6,0x260),(7,0x268))}
        party.append({'partyIndex':index,'internalName':top_name,'displayName':display,
           'creDeathVariable':death,'classRaw':cre[0x273],
           'savedCreScriptResrefs':saved_scripts,
           'weaponQuickslots':{str(x):contents[x] for x in range(35,39)},
           'backpack':{str(x):contents[x] for x in range(18,34)},
           'topSlotItems':contents,
           'selectedWeaponRaw':_num(slots,76,'H')})
    return sorted(party,key=lambda x:x['partyIndex'])

def propose(data:bytes):
    party=read_party(data)
    candidates=[]
    for p in party:
        if p['partyIndex']==0:continue
        for k,v in p['backpack'].items():
            # Demo pilot item is deliberately exact and sourced from a genuine saved actor.
            if not v or v['resref']!='STAF01':continue
            if sum(1 for vv in p['topSlotItems'].values() if vv and vv['resref']=='STAF01')!=1:
                continue
            if p['weaponQuickslots']['35'] is not None:continue
            if p['classRaw']!=3:continue
            candidates.append({'actor':{'partyIndexSnapshot':p['partyIndex'],'internalNameFromGAM':p['internalName'],
              'displayName':p['displayName'],'classRaw':p['classRaw'],'deathVariable':p['creDeathVariable'],
              'savedCreScriptResrefs':p['savedCreScriptResrefs'],
              'scriptAssignmentEvidence':'SAVED_CRE_V1_ONLY_NOT_LIVE_EEEX'},
              'source':{'resref':'STAF01','slot':int(k),'slotIds':f'SLOT_MISC{int(k)-15}',
              'charges':v['charges'],'flags':v['flags'],'expiry':v['expiry']},
              'target':{'slot':35,'slotIds':'SLOT_WEAPON0','statusInSave':'EMPTY'},
              'actorHasUniqueResrefInSavedTopLevelSlots':True})
    return {'schema':'BGXAI_GAM_REAL_PILOT_EVIDENCE_RO_V1','status':'HOLD_RUNTIME_IDENTITY_AND_GAME_PREFLIGHT',
      'gamHeader':'GAMEV2.0','sourceGamSha256':hashlib.sha256(data).hexdigest(),
      'sourceGamBytes':len(data),'partyMembers':len(party),'candidates':candidates,
      'provenBySave':['source item resref and container slot','empty target in saved CRE',
           'saved actor class raw','saved party position','item charges flags expiration',
           'five saved CRE V1.0 script resrefs (not current executing BCS)'],
      'notProvenBySave':['runtime actor instance identity','currently loaded session equals input save',
           'item resource ITM availability/usable by class/kit','actor-specific arming scope',
           'active manual/EPS/current action','native V2 compile','live item move and conservation',
           'live EEex assigned BCS level 1/2, current script execution or script slot ownership'],
      'pilotExecutable':False,'manifestExecutable':False,'gameModified':False,'ordersSent':0}

def main():
    p=argparse.ArgumentParser();p.add_argument('gam',type=Path);p.add_argument('--json',type=Path)
    a=p.parse_args()
    if a.gam.is_symlink() or not a.gam.is_file():raise SystemExit('HOLD_NOT_A_REGULAR_FILE')
    b=a.gam.read_bytes()
    try:r=propose(b)
    except (Hold,struct.error,UnicodeDecodeError) as e:
        r={'status':'HOLD_GAM_PARSER','reason':str(e),'gameModified':False,'ordersSent':0}
    s=json.dumps(r,ensure_ascii=False,indent=2)
    if a.json:a.json.write_text(s+'\n',encoding='utf-8')
    print(s)
    return 0 if r['status']=='HOLD_RUNTIME_IDENTITY_AND_GAME_PREFLIGHT' else 3

if __name__=='__main__':raise SystemExit(main())