local script='/mnt/data/BGXAI_WEAPON_RUNTIME_V1/M_BGXWP.lua'
local passed=0
local function test(name,fn) local ok,err=pcall(fn); if not ok then error('FAIL '..name..': '..tostring(err)) end; passed=passed+1;print('PASS '..name) end
local function setup(opts)
 opts=opts or {}
 local data,registered,actions={},nil,0
 local userdata={flushes=0,writes=0,closed=0}
 local handle={}
 function handle:write(...) userdata.writes=userdata.writes+1;data[#data+1]=table.concat({...},'') end
 function handle:flush() userdata.flushes=userdata.flushes+1 end
 function handle:close() userdata.closed=userdata.closed+1 end
 local openpath
 local fakeio={open=function(path,mode)
  openpath=path;assert(mode=='a')
  if opts.no_file then return nil end
  return handle
 end}
 local fakeos={getenv=function(k) if opts.no_home then return nil end; assert(k=='USERPROFILE');return 'C:\\Users\\Drevo' end,
  date=function() return '2026-11-21T11:00:00Z' end}
 local sprite={m_id=77,m_equipment={m_selectedWeapon=10},m_bAllowEffectListCall=1,m_curScriptNum=3,
  m_derivedStats={},}
 local stats={m_nNumberOfAttacks=-2,m_nSTR=18,m_nSTRExtra=80,m_nDEX=16,
  m_nTHAC0=8,m_nDamageBonus=5,m_nMeleeDamageBonus=2,
  m_nMissileDamageBonus=7,m_nMissileTHAC0Bonus=-3,m_bImprovedHaste=1}
 local env={io=fakeio,os=fakeos,EEex_Sprite_GetInPortraitID=function(i) if i==2 then return 77 end;return -1 end,
  EEex_Sprite_GetActiveStats=function(x) if opts.stats_unavailable then error('stats unavailable') end;assert(x==sprite);return stats end,
  EEex_Action_AddSpriteStartedActionListener=function(fn) registered=fn end,
  math=math,pcall=pcall,type=type,tostring=tostring,table=table,string=string,pairs=pairs}
 if opts.missingEEex then env.EEex_Action_AddSpriteStartedActionListener=nil end
 setmetatable(env,{__index=_G})
 assert(loadfile(script,'t',env))()
 return {module=env.BGXWeaponRuntimeR1,listener=function()return registered end,
  data=data,stats=stats,sprite=sprite,openpath=function()return openpath end,
  calls=userdata,env=env}
end

test('registers one callback, no combat action',function()
 local x=setup();assert(x.module.registered==true and type(x.listener())=='function')
 assert(x.module.recorded==0 and x.calls.writes==1)
end)
test('uses established reports directory',function()
 local x=setup();assert(x.openpath()=='C:\\Users\\Drevo\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl')
end)
test('captures verified fields as RAW only',function()
 local x=setup();x.listener()(x.sprite,{m_actionID=3})
 local l=x.data[2];assert(l:find('"aprRaw":-2',1,true));assert(l:find('"improvedHasteRaw":1',1,true))
 assert(l:find('"selectedWeaponRaw":10',1,true));assert(l:find('"actualPerSlotAPRVerified":false',1,true))
end)
test('buff update re-observed without cancelling action',function()
 local x=setup();x.listener()(x.sprite,{m_actionID=3});x.stats.m_bImprovedHaste=0;x.listener()(x.sprite,{m_actionID=3})
 assert(x.data[3]:find('"improvedHasteRaw":0',1,true));assert(x.module.recorded==2)
end)
test('other creatures ignored',function()
 local x=setup();x.listener()({m_id=55},{m_actionID=3});assert(x.module.recorded==0)
end)
test('null for inaccessible derived values',function()
 local x=setup({stats_unavailable=true});x.listener()(x.sprite,{m_actionID=3})
 assert(x.data[2]:find('"aprRaw":null',1,true))
end)
test('no report directory = no registration',function()
 local x=setup({no_file=true});assert(x.module.registered==false and not x.listener());assert(x.module.writer=='REPORT_DIRECTORY_UNAVAILABLE')
end)
test('no userprofile = no report file',function()
 local x=setup({no_home=true});assert(x.module.registered==false and x.openpath()==nil)
end)
test('no EEex = no listener',function()
 local x=setup({missingEEex=true});assert(x.module.registered==false and not x.listener())
end)
test('duplicate load does not double-register',function()
 local x=setup();local cb=x.listener();assert(loadfile(script,'t',x.env))();assert(x.listener()==cb)
end)
test('caps capture count without changing actions',function()
 local x=setup();for i=1,326 do x.listener()(x.sprite,{m_actionID=3}) end
 assert(x.module.recorded==320);assert(x.module.skipped==6);assert(x.calls.writes==321)
end)
test('source contains no commands, no current-action mutation',function()
 local data=assert(io.open(script,'r')):read('*a');assert(not data:find('ClearActions%('))
 assert(not data:find('SelectWeaponAbility%('))
 assert(not data:find('SetGlobal%('))
 assert(not data:find('Stop%('))
end)
print('BGXWP_OBSERVER_TESTS '..passed..'/12 PASS')
