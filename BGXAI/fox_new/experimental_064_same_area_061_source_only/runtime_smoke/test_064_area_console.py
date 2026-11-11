"""Actual Lua 5.4 compilation/execution of 1-line 064 EEex smoke, no game writes."""
import unittest
from pathlib import Path
from lua64_harness import run_case
ROOT=Path(__file__).resolve().parent
F=ROOT/'BGX64_AREA_CONSOLE_ONE_LINE.lua'
# Standalone console text is executable, not a require-able module.
class ConsoleSmoke(unittest.TestCase):
    def execute(self, prep, test):
        # use run_case's source wrapper; the console code runs automatically
        # during module execution. It does not call any game-state mutators.
        base='''
local A={} local B={}
local objs={ [100]={m_id=100,m_pArea=A}, [101]={m_id=101,m_pArea=A}, [102]={m_id=102,m_pArea=B} }
local p={[0]=100,[1]=101,[2]=102}
function EEex_Sprite_GetInPortraitID(i) return p[i] end
function EEex_GameObject_Get(id) return objs[id] end
function EEex_UDEqual(a,b) return a==b end
C={DisplayText=function(self,text) OUT=text end}
function Attack(...) error('MUTATION')end
function setLocalInt(...) error('MUTATION')end
function EEex_Sprite_AddBlockWeaponHitListener(...) error('HOOK')end
'''
        run_case(base+prep, test, source_file=F)
    def test_valid_sample(self):
        self.execute('', '''assert(OUT=='BGX64 AREA api=true self=3 same=1 diff=2 errors=0')''')
    def test_missing_api(self):
        self.execute('EEex_UDEqual=nil', '''assert(OUT=='BGX64 AREA api=false self=0 same=0 diff=0 errors=0')''')
    def test_duplicate_portrait_excluded(self):
        self.execute('p[1]=p[0];p[2]=nil', '''assert(OUT=='BGX64 AREA api=true self=1 same=0 diff=0 errors=0')''')
    def test_comparison_errors_counted(self):
        self.execute('EEex_UDEqual=function(a,b)error("Bad API")end','''assert(OUT=='BGX64 AREA api=true self=0 same=0 diff=0 errors=3')''')
    def test_empty_party_no_mutation(self):
        self.execute('p={}', '''assert(OUT=='BGX64 AREA api=true self=0 same=0 diff=0 errors=0')''')

if __name__=='__main__':unittest.main()
