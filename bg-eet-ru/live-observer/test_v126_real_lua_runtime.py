"""Run the Lua UI probe on real Lua 5.4 (not EEex/game runtime)."""
from pathlib import Path
import tempfile
import subprocess
from visible_row_guarded_v1 import lua_observer

def main():
    with tempfile.TemporaryDirectory(prefix="V126_REAL_LUA_") as d:
        out=Path(d)/"lines.tsv"
        source=Path(d)/"observer_test.lua"
        test=r'''
io=nil -- Simulate Beamdog UI default: io library is NOT loaded.
local seen={}
print=function(line) seen[#seen+1]=line end
local text='Халид промахивается'
assert(BG_EET_RU_V126_RowRecord(9,text)==text)
assert(BG_EET_RU_V126_RowRecord(9,text)==text)
assert(#seen==1)
assert(seen[1]:find('BG_EET_RU_V126_ROW',1,true))
assert(seen[1]:find('9',1,true))
assert(BG_EET_RU_V126_RowRecord(10,17)==17)
assert(BG_EET_RU_V126_RowRecord(nil,text)==text)
assert(BG_EET_RU_V126_RowRecord(-1,text)==text)
assert(BG_EET_RU_V126_RowRecord(11,'Новое сообщение')=='Новое сообщение')
assert(#seen==2)
for i=12,400 do BG_EET_RU_V126_RowRecord(i,'test'..i) end
assert(BG_EET_RU_V126_RowState.count==160)
assert(#seen==160)
assert(BG_EET_RU_V126_RowState.failures==0)
io=io -- still nil
'''
        source.write_text(lua_observer(out)+test,encoding="utf8")
        p=subprocess.run(["lua5.4",str(source)],capture_output=True,text=True,timeout=20)
        if p.returncode:
            raise RuntimeError("V126_REAL_LUA_FAIL:"+p.stdout[-500:]+p.stderr[-500:])
        assert not out.exists(), "IO output must be absent when standard io is missing"
        print("V126_REAL_LUA_UI_NO_IO_PASS 160 bounded rows; original value preserved")

if __name__=="__main__":
    main()
