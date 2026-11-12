"""Reproduce source-only 066S candidate from exact verified 066; never write game."""
from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).parent
BASE=ROOT/'M_BX43_066_BASELINE_READONLY.lua'
SOURCE=ROOT/'BGX66_CASTER_SUPPORT.lua'
OUT=ROOT/'M_BX43_066S_CASTER_CANDIDATE.lua'
PIN066='c66ebb5190be8103819106a48d3100055b5791adf7c2d1df5f3e54596823540b'

def build():
    base=BASE.read_bytes()
    if sha256(base).hexdigest()!=PIN066:raise ValueError('STOP: exact 066 source changed')
    a=base.decode('utf-8');b=SOURCE.read_text(encoding='utf-8')
    needle='\nP.init()\n'
    if a.count(needle)!=1:raise ValueError('STOP: P.init hook drift')
    result=a.replace(needle,'\n'+b+needle,1).encode('utf-8')
    for t in ('EEex_Sprite_AddBlockWeaponHitListener','EEex_Action_AddSpriteStartedActionListener','function P.onWeaponHit(context)'):
        if result.count(t.encode())!=base.count(t.encode()):raise ValueError('STOP: listener drift: '+t)
    if result.replace(('\n'+b).encode(),b'',1)!=base:raise ValueError('STOP: nonreversible delta')
    return result
if __name__=='__main__':
    c=build();OUT.write_bytes(c)
    print('BUILT_066S SHA256='+sha256(c).hexdigest()+' BYTES='+str(len(c)))
