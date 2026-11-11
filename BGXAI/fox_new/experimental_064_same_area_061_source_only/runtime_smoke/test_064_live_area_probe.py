"""Native Lua5.4 execution tests for read-only live EEex area API probe."""
import unittest
from pathlib import Path
from lua64_harness import run_case

SOURCE = Path(__file__).with_name('BGX64_LIVE_AREA_PROBE.lua')

BASE = r'''
local objects={}
local P={}
local A={}
local B={}
function new(id,area) return {m_id=id,m_pArea=area} end
objects[100]=new(100,A);objects[101]=new(101,A);objects[102]=new(102,B)
P[0]=100;P[1]=101;P[2]=102
function EEex_Sprite_GetInPortraitID(i) return P[i] end
function EEex_GameObject_Get(id) return objects[id] end
function EEex_UDEqual(a,b) return a==b end
function setLocalInt(...) error('FORBIDDEN_MUTATION') end
function Attack(...) error('FORBIDDEN_ATTACK') end
function ProtectObject(...) error('FORBIDDEN_PROTECT') end
function EEex_Sprite_AddBlockWeaponHitListener(...) error('FORBIDDEN_HOOK') end
'''

class LiveAreaNative(unittest.TestCase):
    def case(self, pre='', assertions=''):
        run_case(BASE+pre, assertions, source_file=SOURCE)
    def test_proves_same_and_different_area(self):
        self.case('', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SAME_AREA_API_CONFIRMED')
          assert(r.api==true and r.valid_sprites==3 and r.self_true==3)
          assert(r.pair_true==1 and r.pair_false==2 and r.pair_failed==0)
          assert(r.install_authorized==false)
          assert(BGXMODULE.message(r):find('BGX64 area=SAME_AREA_API_CONFIRMED',1,true))
        ''')
    def test_api_unavailable_fails_closed(self):
        self.case('EEex_UDEqual=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='API_UNAVAILABLE' and r.install_authorized==false)
        ''')
    def test_no_portraits_fails_closed(self):
        self.case('P={}', '''
          local r=BGXMODULE.probe()
          assert(r.status=='NO_VALID_GAME_SPRITES')
        ''')
    def test_self_comparison_error_fails_closed(self):
        self.case('EEex_UDEqual=function(a,b)error("disabled")end', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_EQUALITY_FAILED' and r.self_failed==3)
        ''')
    def test_self_false_fails_closed(self):
        self.case('EEex_UDEqual=function(a,b)return false end', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_EQUALITY_FAILED' and r.pair_true==0)
        ''')
    def test_one_sprite_self_only_not_full_confirmed(self):
        self.case('P[1]=nil;P[2]=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR' and r.self_true==1)
        ''')
    def test_cross_area_only_self_only(self):
        self.case('P[1]=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR' and r.pair_false==1)
        ''')
    def test_duplicate_portrait_does_not_fake_pair(self):
        self.case('P[1]=P[0];P[2]=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR')
        ''')
    def test_missing_object_does_not_crash(self):
        self.case('objects[101]=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR' and r.valid_sprites==2)
        ''')
    def test_bad_identity_does_not_crash(self):
        self.case('objects[101].m_id=200', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR' and r.valid_sprites==2)
        ''')
    def test_missing_field_does_not_crash(self):
        self.case('objects[101].m_pArea=nil', '''
          local r=BGXMODULE.probe()
          assert(r.status=='SELF_ONLY_NO_IN_AREA_PAIR' and r.valid_sprites==2)
        ''')
    def test_paired_comparison_error_fails_closed(self):
        self.case('EEex_UDEqual=function(a,b)if a~=b then error("cross") end return true end', '''
          local r=BGXMODULE.probe()
          assert(r.status=='PAIR_COMPARISON_FAILED' and r.pair_true==1 and r.pair_failed==2)
        ''')

if __name__=='__main__':unittest.main()
