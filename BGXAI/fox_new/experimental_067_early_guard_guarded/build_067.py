"""Read-only deterministic source-only build over exact installed 066S."""
from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).resolve().parent
BASE=ROOT/'M_BX43_066S_CASTER_CANDIDATE.lua'
EXT=ROOT/'BGX67_PREHIT_GUARD.lua'
OUT=ROOT/'M_BX43_067_EARLY_CANDIDATE.lua'
PIN066S='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
def build():
 base=BASE.read_bytes();addon=EXT.read_bytes()
 if sha256(base).hexdigest()!=PIN066S:raise ValueError('BASE_NOT_INSTALLED_066S_HASH')
 needle=b'\nP.init()\n'
 if base.count(needle)!=1:raise ValueError('INIT_ANCHOR_DRIFT')
 res=base.replace(needle,b'\n'+addon+needle,1)
 if res.replace(b'\n'+addon,b'',1)!=base:raise ValueError('NONREVERSIBLE_ADDON')
 for name in (b'EEex_Action_AddSpriteStartedActionListener, P.onStarted',b'EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'):
  if res.count(name)!=base.count(name):raise ValueError('REGISTERED_LISTENER_CHANGED')
 return res
if __name__=='__main__':
 x=build();OUT.write_bytes(x);print('067_EARLY_LUA_SHA256',sha256(x).hexdigest(),len(x))
