import unittest
from pathlib import Path
from lua64_harness import run_case
SRC=Path(__file__).with_name('BGX64_AREA_QUICK_CONSOLE.lua')
BASE='''
local one={} local other={}
local objects={[1]={m_pArea=one},[2]={m_pArea=one}}
function EEex_Sprite_GetInPortraitID(i) return i+1 end
function EEex_GameObject_Get(id) return objects[id] end
function EEex_UDEqual(a,b) return a==b end
C={DisplayText=function(_,v) OUTPUT=v end}
function Attack(...)error('FORBIDDEN')end
function ClearActions(...)error('FORBIDDEN')end
'''
class QuickArea(unittest.TestCase):
    def runlua(self, pre, expected):
        run_case(BASE+pre, f'assert(OUTPUT=={expected!r})',source_file=SRC)
    def test_same_area(self):
        self.runlua('','BGX64 AREACHECK true true')
    def test_different_area(self):
        self.runlua('objects[2].m_pArea=other','BGX64 AREACHECK true false')
    def test_missing_api(self):
        self.runlua('EEex_UDEqual=nil','BGX64 AREACHECK false error')
    def test_missing_sprite(self):
        self.runlua('objects[2]=nil','BGX64 AREACHECK false error')
if __name__=='__main__':unittest.main()
