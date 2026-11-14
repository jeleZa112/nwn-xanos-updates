"""Strict SHA and diff verification for *source only* EPS-first 066S patch."""
from pathlib import Path
import difflib, hashlib, json
from arbiter_exact_diff import verify_exact_revert
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'manifest_sha256.json').read_text(encoding='utf-8'))
assert m['status']=='SOURCE_ONLY_NOT_INSTALLED'
assert m['installed_lua_sha256']=='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
for f,h in m['files'].items():
 p=ROOT/f
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h, 'BAD_FILE_'+f
assert verify_exact_revert(ROOT)
original=(ROOT/'M_BX43_066S_CASTER_CANDIDATE.lua').read_text(encoding='utf-8')
prior=(ROOT/'M_BX43_066S_CAPABILITY_PRE_ARBITRATION.lua').read_text(encoding='utf-8')
new=(ROOT/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').read_text(encoding='utf-8')
assert hashlib.sha256(original.encode()).hexdigest()==m['installed_lua_sha256']
assert hashlib.sha256(prior.encode()).hexdigest()=='954bb400ccc7e39aa0040460d167b51584892d7bd58237bf78ed05781eb7da70'
assert hashlib.sha256((ROOT/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf').read_bytes()).hexdigest()=='c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae'
diff=''.join(difflib.unified_diff(original.splitlines(True),new.splitlines(True),fromfile='LIVE_066S_SHA_50640902',tofile='SOURCE_ONLY_CAPABILITY_GUARD_HEAL_PRIORITY'))
assert (ROOT/'066S_capability_patch.diff').read_text(encoding='utf-8')==diff
small_diff=''.join(difflib.unified_diff(prior.splitlines(True),new.splitlines(True),fromfile='PRIOR_SOURCE_ONLY_V2',tofile='SOURCE_ONLY_WITH_SHARED_RESERVATIONS'))
assert (ROOT/'guardian_heal_priority_only.diff').read_text(encoding='utf-8')==small_diff
for marker in ('EEex_Action_AddSpriteStartedActionListener, P.onStarted','EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit','BGX52Bridge.prepare=T.prepare','BGX66Caster.onHit(hit)'):
 assert original.count(marker)==new.count(marker), marker
assert original.count('ClearActions(')==new.count('ClearActions(')==0
assert new.count('T.capabilitySourceVerified = false')==1
assert new.count('T.capabilityVerifier = nil')==1
assert new.count('S.capabilityVerifier = nil')==1
assert not any(ROOT.glob('*.bcs')) and not any(ROOT.glob('*.tp2')) and not any(ROOT.glob('*.exe'))
print(f'PASS: {len(m["files"])} SHA256, exact old 066S, BAF exact, diff exact, 5 approved arbitration changes, no game installer')