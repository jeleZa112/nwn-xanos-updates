-- Test harness run with real liblua5.4, mocking only EEex engine interactions.
local file = assert(arg and arg[1], "Need policy path")
assert(loadfile(file))()
local E = BGX59Eligibility
local area1, area2 = {}, {}
local visible = {}
local sightFails = false
EEex_UDEqual = function(a,b) return rawequal(a,b) end
EEex_Sprite_ForAllOfTypeStringInRange = function(guardian, typ, radius, cb, useLos, sprites)
    assert(typ == "[ANYONE]" and radius == 128 and useLos == true and sprites == false)
    if sightFails then error("synthetic EEex range failure") end
    for _, v in ipairs(visible[guardian.m_id] or {}) do cb(v) end
end
local function sprite(id,area) return {m_id=id,m_pArea=area} end
local victim = sprite(31,area1)
local exterior = sprite(41,area2)
local localGuard = sprite(42,area1)
local localFar = sprite(43,area1)
visible[42]={victim}
visible[43]={}
local function option(s,slot,dist) return {sprite=s,id=s.m_id,slot=slot,dist=dist} end
local n=0
local function check(label, fn) fn();n=n+1;print("PASS",label) end
check("cross-area guard is refused",function()
 local selected,reason=E.choose(victim,{option(exterior,4,1)})
 assert(selected==nil and reason=="no_guardian_same_area",tostring(reason))
end)
check("nearby same-area guard selected instead of closer cross-area",function()
 local selected,reason=E.choose(victim,{option(exterior,4,1),option(localGuard,2,12)})
 assert(selected.id==42 and reason=="selected")
end)
check("same area without LOS refused",function()
 local selected,reason=E.choose(victim,{option(localFar,5,1)})
 assert(selected==nil and reason=="no_guardian_visible_nearby",tostring(reason))
end)
check("invalid area refused",function()
 local selected,reason=E.choose(victim,{option(sprite(50,nil),4,2)})
 assert(selected==nil and reason=="no_guardian_visible_nearby")
end)
check("missing line-of-sight API fails closed",function()
 local backup=EEex_Sprite_ForAllOfTypeStringInRange
 EEex_Sprite_ForAllOfTypeStringInRange=nil
 local selected,reason=E.choose(victim,{option(localGuard,2,2)})
 assert(selected==nil and reason=="no_guardian_visible_nearby")
 EEex_Sprite_ForAllOfTypeStringInRange=backup
end)
check("LOS execution failure fails closed",function()
 sightFails=true
 local selected=E.choose(victim,{option(localGuard,2,2)})
 assert(selected==nil)
 sightFails=false
end)
check("deterministic tie broken by portrait slot",function()
 visible[43]={victim}
 local selected=E.choose(victim,{option(localFar,5,2),option(localGuard,2,2)})
 assert(selected.id==42)
end)
check("no candidates leaves request absent",function()
 local selected,reason=E.choose(victim,{})
 assert(selected==nil and reason=="no_f_mode_guardian")
end)
check("helper has no LOCALS write / combat dispatch symbols",function()
 local src=assert(io.open(file,"rb")):read("*a")
 for _,word in ipairs({"setLocalInt(", "ProtectObject(", "ClearActions(","ActionOverride(","Attack("}) do
  assert(not src:find(word,1,true),"unsafe symbol: "..word)
 end
end)
print("PASS",n,"tests")
