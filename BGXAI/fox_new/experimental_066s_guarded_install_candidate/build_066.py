"""Build deterministic 066 from *exact* user-verified 064 source. Source-only; never touch game."""
from pathlib import Path
from hashlib import sha256
P=Path(__file__).parent
BASE=P/'M_BX43_064_BASELINE_READONLY.lua'
POLICY=P/'BGX66_TEAM_BRIDGE.lua'
OUT=P/'M_BX43_066_CANDIDATE.lua'
PIN064='bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b'
VERSION='0.3.32-066-MULTI-FRONTLINE-GUARDED'
def digest(data):return sha256(data).hexdigest()
def build():
    raw=BASE.read_bytes()
    if digest(raw)!=PIN064:raise ValueError('STOP: 064 BASELINE HASH DRIFT')
    s=raw.decode('utf-8');needle='\nP.init()\n'
    if s.count(needle)!=1:raise ValueError('STOP: init hook changed')
    old='P.version = "0.3.29-064-061-SAME-AREA-GUARD-SOURCE"'
    if s.count(old)!=1:raise ValueError('STOP: 064 VERSION changed')
    policy=POLICY.read_bytes().decode('utf-8')
    assert policy.rstrip().endswith('BGX52Bridge.prepare=T.prepare')
    output=s.replace(old,'P.version = "'+VERSION+'"',1).replace(needle,'\n'+policy+needle,1).encode('utf-8')
    if output.count(b'EEex_Sprite_AddBlockWeaponHitListener')!=raw.count(b'EEex_Sprite_AddBlockWeaponHitListener') or output.count(b'EEex_Action_AddSpriteStartedActionListener')!=raw.count(b'EEex_Action_AddSpriteStartedActionListener'):
        raise ValueError('STOP: listener count drift')
    if output.count(b'function P.onWeaponHit(context)')!=1 or output.count(b'P.init()')!=2:
        raise ValueError('STOP: changed listener call')
    if output.replace(('\n'+policy).encode('utf-8'),b'',1).replace(('P.version = "'+VERSION+'"').encode(),old.encode(),1)!=raw:
        raise ValueError('STOP: nonreversible patch')
    return output
if __name__=='__main__':
    c=build();OUT.write_bytes(c)
    print('BUILT_066 sha256='+digest(c)+' bytes='+str(len(c)))
