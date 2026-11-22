"""Create a reduced SOURCE-ONLY Lua fixture from the already verified 16-action log.

Never accesses game, Windows, GitHub, saves, or the network. Does not change input.
"""
import json,hashlib,pathlib,collections
SOURCE=pathlib.Path('/mnt/data/BGXAI_WEAPON_CONSOLE_20261122T131454167969Z.log')
TARGET=pathlib.Path(__file__).with_name('BGXAI_R6_LIVE_REDUCED_FIXTURE_20261122.lua')
expected='174cec7f72f9f1c3aed717484bb3606832aa0cbfca1ad6d6d9bc3cd4583199db'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==expected
records=collections.defaultdict(list)
for line in SOURCE.read_text(encoding='utf-8').splitlines():
    for name,key,kind in [('BGXW4','ACTIVE','r4'),('BGXW2','SLOTS','r2'),('BGXWP','ACTION','r1')]:
        prefix=f'INFO: LUA: [{name}] '
        if line.startswith(prefix):
            o=json.loads(line[len(prefix):]);typ=o.get('type','ACTION' if name=='BGXWP' else None)
            if typ==key:records[kind].append(o)
assert all(len(records[k])==16 for k in ['r4','r2','r1'])

def lua(v):
    if v is None:return 'nil'
    if v is False:return 'false'
    if v is True:return 'true'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=True)
    if isinstance(v,(int,float)):return repr(v)
    if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
    if isinstance(v,dict):return '{'+','.join(f'[{lua(k)}]={lua(x)}' for k,x in v.items())+'}'
    raise TypeError(type(v))

parts=[]
for a,b,c in zip(records['r4'],records['r2'],records['r1']):
    assert a['actor']==b['actor']==c['actor'] and a['selectedWeaponRaw']==b['selectedWeaponRaw']==c['selectedWeaponRaw']
    x={k:a[k] for k in ['schema','type','status','seq','actor','partyIndex','actionRaw','selectedWeaponRaw','presentCount','missingCount','allBuffsObserved','allEffectsObserved','alternateSlotAPRVerified','manualOrderProven','epsQueueProven','weaponSwitchAuthorized','dispatchAuthorized']}
    x['statsRaw']={k:a['statsRaw'][k] for k in ['m_nNumberOfAttacks','m_nTHAC0']}
    y={k:b[k] for k in ['schema','type','seq','actor','partyIndex','actionRaw','selectedWeaponRaw','quickWeapons','quivers']}
    z={k:c[k] for k in ['type','sequence','actor','partyIndex','action','selectedWeaponRaw','aprRaw','thac0Raw']}
    parts.append({'r4':x,'r2':y,'r1':z})
result='-- Reduced live fixture from original user console SHA256 '+expected+'\n-- Selected fields preserved exactly. Not proof of missing unrepresented fields.\nreturn '+lua(parts)+'\n'
TARGET.write_text(result,encoding='utf-8')
print('REAL_FIXTURE_OK',len(parts),TARGET.stat().st_size,TARGET)
