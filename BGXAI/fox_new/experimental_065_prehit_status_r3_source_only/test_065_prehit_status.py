"""Pure console smoke test for already-installed BGX43Probe: NO hook registration/writes."""
import unittest
from pathlib import Path
from lua65_harness import run_case
P = Path(__file__).resolve().parent/'BGXAI65_PREHIT_STATUS_READONLY.lua'

def case(preamble, assertions):
    run_case('output={};C={DisplayText=function(_,s)table.insert(output,s)end};'+preamble, assertions, P)

class PreHitStatusTests(unittest.TestCase):
    def test_no_observer(self):
        case('',"assert(#output==1 and output[1]=='BGX65PRE NO_OBSERVER')")
    def test_empty_observer(self):
        case('BGX43Probe={installed=true,seenActions=3,attackCandidates=0,weaponHitCalls=0,weaponHitRegistered=true}',
             "assert(#output==3 and output[2]=='BGX65PRE lastAction=NONE' and output[3]=='BGX65PRE lastHit=NONE')")
    def test_unverified_action_not_claimed_confirmed(self):
        case("BGX43Probe={installed=true,lastAttack={action_id=134,reason='target_unresolved',target_source='none'}}",
             "assert(output[2]:find('target_unresolved') and not output[2]:find('confirmed'))")
    def test_recorded_action_and_hit_remain_separate(self):
        case("BGX43Probe={installed=true,lastAttack={action_id=134,reason='recorded',target_source='actee2',actor_id=999,target_id=102,target1=false,target2=102,sprite_target=102},lastWeaponHit={reason='recorded',actor_id=999,target_id=102}}",
             "assert(#output==3 and output[2]:find('source=actee2') and output[2]:find('victim=102') and output[3]:find('lastHit=recorded'))")
    def test_bad_object_does_not_write(self):
        case("BGX43Probe={installed=false,lastAttack=4,lastWeaponHit='bad'}",
             "assert(#output==3 and output[2]=='BGX65PRE lastAction=NONE' and output[3]=='BGX65PRE lastHit=NONE')")
    def test_no_engine_mutations_in_source(self):
        t=P.read_text('utf-8')
        for x in ('EEex_Action_AddSpriteStartedActionListener(', 'EEex_Sprite_AddBlockWeaponHitListener(', 'setLocalInt(',
                  'Attack(', 'Spell(', 'ClearActions(', 'MoveToObject(', 'SetGlobal(', 'io.', 'os.'):
            self.assertNotIn(x,t)
        self.assertIn('BGX43Probe',t)

if __name__=='__main__': unittest.main()
