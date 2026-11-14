"""Read-only archive file-integrity and source-diff check, never touches game.
Native behavior tests are in run_regression.py, not this verifier.
"""
from __future__ import annotations
from pathlib import Path
import difflib, hashlib, json, re
HERE=Path(__file__).resolve().parent
man=json.loads((HERE/'manifest_sha256.json').read_text(encoding='utf-8'))
assert man['installed_lua_sha256']=='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
assert man['status']=='SOURCE_ONLY_NOT_INSTALLED'
for name,expected in man['files'].items():
    p=HERE/name
    assert p.is_file(), 'MISSING:'+name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected, 'DRIFT:'+name
old=(HERE/'M_BX43_066S_CASTER_CANDIDATE.lua').read_text(encoding='utf-8')
prior=(HERE/'M_BX43_066S_HEAL_PATCH_PREVIOUS.lua').read_text(encoding='utf-8')
new=(HERE/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').read_text(encoding='utf-8')
assert hashlib.sha256(old.encode()).hexdigest()==man['installed_lua_sha256']
assert hashlib.sha256(prior.encode()).hexdigest()=='c4e25bf6de7c3569b03657f3d48b5ddc9730c94ac6f63124bcc3f32cfb471e29'
# Reconstruct only additive guard gate and one selector expression (all other
# lines must be exactly the previously tested previous heal patch).
start=new.index('-- Optional role-verified intercept extension; default OFF keeps 066S byte-for-byte policy.')
end=new.index('local SUPPORT = {',start)
restored=new[:start]+new[end:]
restored=restored.replace('if verifiedGuardAbility(obj,role,attackerID,victimID,seq) and validGuardian(obj) and not T.reservations[id] then',
                          "if role=='frontline' and validGuardian(obj) and not T.reservations[id] then",1)
assert restored==prior,'UNEXPECTED_066S_CODE_CHANGE'
assert new.count('T.capabilitySourceVerified = false')==1
assert new.count('T.capabilityVerifier = nil')==1
assert new.count('S.capabilityVerifier = nil')==1
for marker in ['EEex_Action_AddSpriteStartedActionListener, P.onStarted','EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit',
               'BGX52Bridge.prepare=T.prepare','BGX66Caster.onHit(hit)']:
    assert old.count(marker)==new.count(marker),'LISTENER_OR_HOOK_DIFF:'+marker
assert 'ClearActions(' not in new
expected=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='LIVE_066S_SHA_50640902',tofile='SOURCE_ONLY_CAPABILITY_GUARD_HEAL'))
assert (HERE/'066S_capability_patch.diff').read_text(encoding='utf-8')==expected,'PATCH_DIFF_UNREPRODUCIBLE'
assert not list(HERE.glob('*.tp2')) and not list(HERE.glob('*.bcs')) and not list(HERE.glob('*.exe')),'INSTALL_ARTIFACT_PRESENT'
print('PASS:',len(man['files']),'SHA256; original 066S exact; previous heal patch exact; only additive guard+heal diff; no installer; SOURCE ONLY')
