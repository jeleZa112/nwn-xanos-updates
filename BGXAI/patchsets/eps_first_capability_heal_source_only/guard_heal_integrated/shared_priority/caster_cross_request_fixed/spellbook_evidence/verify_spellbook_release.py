"""Exact source-only gate: zip files/contents, no game mutation or fake live proof."""
from pathlib import Path
import hashlib,json,difflib,re
R=Path(__file__).resolve().parent
M=json.loads((R/'manifest_spellbook_sha256.json').read_text(encoding='utf-8'))
assert M['status']=='SOURCE_ONLY_NEVER_INSTALLED'
for name,want in M['files'].items():
    path=R/name
    assert path.is_file(),f'missing {name}'
    got=hashlib.sha256(path.read_bytes()).hexdigest()
    assert got==want,f'SHA_MISMATCH {name}: {got} != {want}'
old=(R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').read_text(encoding='utf-8')
new=(R/'M_BX43_066S_EEEX_BOOK_EVIDENCE_CANDIDATE.lua').read_text(encoding='utf-8')
mod=(R/'BGX66_EEEX117_SPELLBOOK_EVIDENCE.lua').read_text(encoding='utf-8')
old_needle="S.capabilityVerifier = nil\nlocal function candidateCanUseSpell(actor, cls, spell)\n  if type(S.capabilityVerifier) == 'function' then\n    local ok, available = pcall(S.capabilityVerifier, actor, spell)"
new_needle=""""""+mod+"""
S.capabilityVerifier = nil
S.requireMemorizedEvidence = false -- only an explicit opt-in may require EEex book proof
local function candidateCanUseSpell(actor, cls, spell)
  if type(S.capabilityVerifier) == 'function' then
    -- Additional read-only book evidence; never authorizes a cast alone.
    local observed = BGX66SpellbookEvidence.read(actor, spell)
    -- Book evidence can deny a cast request, NEVER grant one by itself.
    if S.requireMemorizedEvidence == true and
       (type(observed)~='table' or type(observed.ready_count)~='number'
        or observed.ready_count<1) then return false end
    local ok, available = pcall(S.capabilityVerifier, actor, spell, observed)"""
assert old.count(old_needle)==1
assert new==old.replace(old_needle,new_needle),'UNRELATED_EDIT_IN_NEW_CANDIDATE'
assert (R/'spellbook_evidence_only.diff').read_text(encoding='utf-8')==''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='PRIOR_CROSS_REQUEST_SOURCE_ONLY',tofile='SPELLBOOK_READONLY_EVIDENCE_SOURCE_ONLY'))
legacy=R/'M_BX43_066S_CASTER_CANDIDATE.lua'
assert hashlib.sha256(legacy.read_bytes()).hexdigest()=='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
assert hashlib.sha256((R/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf').read_bytes()).hexdigest()=='c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae'
for banned in (r'\bSpell\s*\(',r'\bAttack\s*\(',r'\bClearActions\s*\(',r'\bsetLocalInt\s*\(',r'EEex_Action_Queue\w*\s*\(',r'\.m_flags\s*='):
    assert re.search(banned,mod)==None,f'NEW_ENGINE_WRITE {banned}'
for marker in ['EEex_Action_AddSpriteStartedActionListener, P.onStarted','EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit','BGX52Bridge.prepare=T.prepare']:
    assert old.count(marker)==new.count(marker)==1,marker
for marker in ['T.capabilitySourceVerified = false','T.capabilityVerifier = nil','S.capabilityVerifier = nil','S.requireMemorizedEvidence = false']:
    assert new.count(marker)==1,marker
assert not any(R.glob('*.bcs')) and not any(R.glob('*.tp2')) and not any(R.glob('*.exe'))
print(f'RELEASE_VERIFY_PASS {len(M["files"])} source SHA-256, exact single substitution, old 066S SHA, no new engine action, SOURCE ONLY')
