import unittest
from lua_harness import run_case, SOURCE

BASE = r'''
local actors = {
 [101]={m_id=101,m_typeAI={m_Class=1},m_curAction={m_actionID=134},m_nModalState=0,
        getLocalInt=function(self,key) return key=='BGX38_GUARD' and 1 or nil end},
 [102]={m_id=102,m_typeAI={m_Class=7},m_curAction={m_actionID=31},m_nModalState=1,
        getLocalInt=function(self,key) return key=='BGX38_GUARD' and 0 or nil end},
}
function EEex_Sprite_GetInPortraitID(i)
  if i==0 then return 101 elseif i==1 then return 102 end
  return nil
end
function EEex_GameObject_Get(id) return actors[id] end
'''

class NativeLuaTests(unittest.TestCase):
    def test_source_unmodified(self):
        self.assertIn("origin = 'BGXAI_062E_SOURCE_ONLY'", SOURCE.read_text(encoding='utf-8'))

    def test_missing_apis(self):
        run_case('', '''local s=BGXMODULE.snapshot(); assert(s.status=='API_UNAVAILABLE'); assert(#s.party==0)''')

    def test_real_execution_two_members(self):
        run_case(BASE, '''
        local s=BGXMODULE.snapshot()
        assert(s.status=='PARTIAL_OBSERVATIONS_ONLY' and #s.party==2)
        assert(s.party[1].slot==1 and s.party[1].id==101)
        assert(s.party[1].class_id==1 and s.party[1].current_action_id==134)
        assert(s.party[2].slot==2 and s.party[2].class_id==7)
        assert(s.party[1].guard_f==1 and s.party[2].guard_f==0)
        assert(s.party[1].equipped_weapon=='unknown' and s.party[1].can_melee=='unknown')
        assert(s.party[1].manual_order_absent=='unknown' and s.party[1].action_queue_idle=='unknown')
        ''')

    def test_duplicate_id_is_skipped(self):
        run_case(BASE+'''EEex_Sprite_GetInPortraitID=function(i) if i==0 or i==1 then return 101 end end''', '''
        local s=BGXMODULE.snapshot(); assert(#s.party==1 and s.party[1].slot==1)
        ''')

    def test_object_identity_mismatch(self):
        run_case(BASE+'''EEex_GameObject_Get=function(id) return {m_id=999} end''', '''
        local s=BGXMODULE.snapshot(); assert(#s.party==0)
        ''')

    def test_broken_accessor_becomes_unknown(self):
        run_case(BASE+'''actors[101].m_typeAI=nil; actors[101].m_curAction=nil; actors[101].getLocalInt=function()error('blocked')end''','''
        local s=BGXMODULE.snapshot(); assert(s.party[1].class_id=='unknown')
        assert(s.party[1].current_action_id=='unknown' and s.party[1].guard_f=='unknown')
        ''')

    def test_out_of_bounds_is_unknown(self):
        run_case(BASE+'''actors[101].m_typeAI.m_Class=-1; actors[101].m_curAction.m_actionID=999999; actors[101].m_nModalState=-1''','''
        local p=BGXMODULE.snapshot().party[1]
        assert(p.class_id=='unknown' and p.current_action_id=='unknown' and p.modal=='unknown')
        ''')

    def test_boolean_and_fraction_are_unknown(self):
        run_case(BASE+'''actors[101].m_typeAI.m_Class=true;actors[101].m_curAction.m_actionID=12.4''','''
        local p=BGXMODULE.snapshot().party[1]
        assert(p.class_id=='unknown' and p.current_action_id=='unknown')
        ''')

    def test_api_error_fail_closed(self):
        run_case(BASE+'''EEex_Sprite_GetInPortraitID=function()error('mock fail')end''','''
        assert(#BGXMODULE.snapshot().party==0)
        ''')

    def test_never_issues_orders(self):
        run_case(BASE+'''
        function ActionOverride()error('forbidden')end
        function ClearActions()error('forbidden')end
        function Attack()error('forbidden')end
        function MoveToObject()error('forbidden')end
        actors[101].setLocalInt=function()error('forbidden')end
        ''','''
        local s=BGXMODULE.snapshot(); assert(#s.party==2)
        ''')

    def test_only_six_portraits(self):
        run_case(BASE+'''EEex_Sprite_GetInPortraitID=function(i) assert(i>=0 and i<=5);return nil end''','''
        assert(#BGXMODULE.snapshot().party==0)
        ''')

if __name__=='__main__':unittest.main()
