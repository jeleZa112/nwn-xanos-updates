"""Precisely reverses TWO additions from the frozen shared-priority 066S candidate.
No game files are edited. This proof is independent of Lua unit tests.
"""
from pathlib import Path
import hashlib
from arbiter_exact_diff import verify_exact_revert

BASE_SHA = 'b339407826b9c0014a4ba8b4d63021aa48897e40af40f5a249bc78f69b407372'

def reverse(root=None):
    root=Path(root or Path(__file__).resolve().parent)
    old=(root/'M_BX43_066S_CAPABILITY_SHARED_PRIORITY.lua').read_text(encoding='utf-8')
    new=(root/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').read_text(encoding='utf-8')
    before_heal="if candidateCanUseSpell(o,cls,'CLERIC_CURE_LIGHT_WOUNDS') and get(o,'BGX66_S_HEAL_SLOT')==0 then"
    after_heal="-- In optional capability mode, another still-pending BCS caster request\n    -- owns this actor even if the short Lua lease expired. Unknown locals deny.\n    if candidateCanUseSpell(o,cls,'CLERIC_CURE_LIGHT_WOUNDS')\n       and get(o,'BGX66_S_HEAL_SLOT')==0\n       and (T.capabilitySourceVerified ~= true or get(o,'BGX66_S_WARD')==0) then"
    before_ward="if m.id==victimID and candidateCanUseSpell(o,cls,'WIZARD_SHIELD') and health<=25 and get(o,'BGX66_S_WARD')==0 then ward=m end"
    after_ward="if m.id==victimID and candidateCanUseSpell(o,cls,'WIZARD_SHIELD')\n       and health<=25 and get(o,'BGX66_S_WARD')==0\n       and (T.capabilitySourceVerified ~= true or get(o,'BGX66_S_HEAL_SLOT')==0) then ward=m end"
    assert hashlib.sha256(old.encode('utf-8')).hexdigest()==BASE_SHA
    assert new.count(after_heal)==1 and new.count(after_ward)==1
    assert new.replace(after_heal,before_heal).replace(after_ward,before_ward)==old
    assert verify_exact_revert(root)
    return True

if __name__=='__main__':
    assert reverse()
    print('PASS: 2 exact caster cross-request edits; 5 previous guard/heal arbitration edits preserved')
