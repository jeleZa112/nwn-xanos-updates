local path=(arg[0] or ''):match('^(.*[/\\])') or './'
local n=0
local function test(name,fn)
 local ok,msg=pcall(fn)
 if not ok then error('TEST_FAIL '..name..' '..tostring(msg)) end
 n=n+1;print('PASS '..name)
end
local function setup(opts)
 opts=opts or {}
 local output,callback,stats={},nil,{}
 local itemset={[35]={m_useCount1=1,cResRef={get=function() return 'BOW05' end}},[12]={m_useCount1=20,cResRef={get=function() return 'AROW01' end}}}
 local sprite={m_id=139135050,m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0,m_items={get=function(self,i)return itemset[i] end}}}
 local env={math=math,table=table,string=string,type=type,pcall=pcall,tostring=tostring,select=select,ipairs=ipairs,pairs=pairs}
 env.EEex_Sprite_GetInPortraitID=function(i)return i==2 and 139135050 or -1 end
 env.EEex_Action_AddSpriteStartedActionListener=function(fn) callback=fn end
 if opts.nohook then env.EEex_Action_AddSpriteStartedActionListener=nil end
 if not opts.noconsole then env.Infinity_Log=function(s)output[#output+1]=s end end
 if opts.file then
  local h={write=function(self,...)
   output[#output+1]=table.concat({...},'')
   end,flush=function()end,close=function()end}
  env.io={open=function(p,mode)assert(mode=='a');return h end}
  env.os={getenv=function()return 'C:\\Users\\Drevo' end,date=function()return '2026-11-21T14:00:00Z' end}
 else env.io={};env.os={} end
 env.print=nil
 local chunk=assert(loadfile(path..'M_BGXW2.lua','t',env))
 chunk()
 return {obj=env.BGXWeaponSlotsRuntimeR2,sprite=sprite,records=output,call=function(a)if callback then callback(sprite,{m_actionID=a}) end end,env=env}
end
test('register console fallback',function()
 local s=setup();assert(s.obj.registered and s.obj.writer=='CONSOLE_FALLBACK')
 assert(s.records[1]:find('SESSION') and s.records[2]:find('READY'))
end)
test('captures live 31-bit actor with 4 slots',function()
 local s=setup();s.call(105);local l=s.records[3]
 assert(l:find('139135050',1,true) and l:find('BOW05',1,true) and l:find('AROW01',1,true))
 assert(l:find('"index":38',1,true) and l:find('"index":14',1,true))
end)
test('no inferred switch permission',function()
 local s=setup();s.call(105)
 assert(s.records[3]:find('"switchAuthorized":false',1,true))
 assert(s.records[3]:find('"perSlotAPRVerified":false',1,true))
end)
test('selected ammo to weapon change',function()
 local s=setup();s.call(105);s.sprite.m_equipment.m_selectedWeapon=35;s.call(134)
 assert(s.records[3]:find('"selectedWeaponRaw":12',1,true))
 assert(s.records[4]:find('"selectedWeaponRaw":35',1,true))
end)
test('file sink avoids console fallback',function()
 local s=setup({file=true});s.call(105)
 assert(s.obj.writer=='FILE');assert(s.records[1]:find('SESSION',1,true))
end)
test('no sink fails closed',function()
 local s=setup({noconsole=true});assert(not s.obj.registered);assert(s.obj.writer=='NO_OUTPUT_SINK')
end)
test('no hook fails closed',function()
 local s=setup({nohook=true});assert(not s.obj.registered);assert(s.obj.writer=='EEEX_HOOK_UNAVAILABLE')
end)
test('other actor ignored',function()
 local s=setup();s.sprite.m_id=567;s.call(105);assert(#s.records==2)
end)
test('caps 64 snapshots',function()
 local s=setup();for i=1,66 do s.call(105) end
 assert(s.obj.recorded==64);assert(s.obj.skipped==2)
end)
test('duplicate load no duplicate registration',function()
 local s=setup();local before=s.obj;assert(loadfile(path..'M_BGXW2.lua','t',s.env))()
 assert(s.env.BGXWeaponSlotsRuntimeR2==before)
end)
print('BGXW2_RUNTIME_OFFLINE '..n..'/10 PASS')
