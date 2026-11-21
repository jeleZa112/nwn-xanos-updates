local source=(arg and arg[1]) or 'M_BGXWP.lua'
local n=0
local function check(label,fn)
 local ok,err=pcall(fn)
 if not ok then error(label..': '..tostring(err)) end
 n=n+1;print('PASS '..label)
end
local function setup(opts)
 opts=opts or {}
 local lines,console={},{}
 local registered,opened,write_count
 write_count=0
 local handle={}
 function handle:write(...)
  write_count=write_count+1
  if opts.file_fails and write_count>=2 then error('DISK_ERROR') end
  lines[#lines+1]=table.concat({...},'')
 end
 function handle:flush() end
 function handle:close() end
 local stats={m_nNumberOfAttacks=-2,m_nSTR=18,m_nSTRExtra=80,m_nDEX=16,
  m_nTHAC0=8,m_nDamageBonus=5,m_nMeleeDamageBonus=2,m_nMissileDamageBonus=7,
  m_nMissileTHAC0Bonus=-3,m_bImprovedHaste=1}
 local sprite={m_id=77,m_equipment={m_selectedWeapon=10},m_curScriptNum=3,m_bAllowEffectListCall=1}
 local env={math=math,tostring=tostring,pcall=pcall,type=type,
  print=opts.no_print and false or function(s)console[#console+1]=s end,
  Infinity_Log=opts.no_log and false or function(s)console[#console+1]=s end,
  EEex_Sprite_GetInPortraitID=function(i) return i==2 and 77 or -1 end,
  EEex_Sprite_GetActiveStats=function(x) assert(x==sprite);return stats end,
  EEex_Action_AddSpriteStartedActionListener=function(fn) registered=fn end,
  io=opts.no_io and false or {open=function(path,mode)
    opened=path;assert(mode=='a')
    if opts.open_fails then return nil end
    return handle
  end},
  os=opts.no_os and false or {getenv=function()return 'C:\\Users\\Drevo' end, date=function()return 'UTC' end}
 }
 if opts.no_io then env.io=false end
 if opts.no_os then env.os=false end
 if opts.no_eeex then env.EEex_Action_AddSpriteStartedActionListener=false end
 if opts.no_print then env.print=false end
 if opts.no_log then env.Infinity_Log=false end
 local loaded=assert(loadfile(source,'t',env));loaded()
 return {env=env,module=env.BGXWeaponRuntimeR1,callback=function()return registered end,
   logs=lines,console=console,sprite=sprite,stats=stats,opened=function()return opened end}
end
check('file sink registers',function()
 local x=setup();assert(x.module.registered and x.module.writer=='APPEND_REPORT_ONLY')
 assert(x.logs[1]:find('SESSION',1,true));assert(x.logs[2]:find('READY',1,true));assert(#x.console==0)
end)
check('file sink expected report path',function()
 local x=setup();assert(x.opened():find('Documents\\BGXAI_LIVE_REPORTS',1,true))
end)
check('raw APR and selected slot',function()
 local x=setup();x.callback()(x.sprite,{m_actionID=3})
 assert(x.logs[3]:find('"aprRaw":-2',1,true));assert(x.logs[3]:find('"selectedWeaponRaw":10',1,true))
 assert(x.logs[3]:find('"weaponSwitchAuthorized":false',1,true))
end)
check('buff change sampled',function()
 local x=setup();x.callback()(x.sprite,{m_actionID=3});x.stats.m_bImprovedHaste=0
 x.callback()(x.sprite,{m_actionID=3});assert(x.logs[4]:find('"improvedHasteRaw":0',1,true))
end)
check('no io uses console',function()
 local x=setup({no_io=true});assert(x.module.registered and x.module.writer=='CONSOLE_FALLBACK')
 assert(#x.console==4);assert(x.console[1]:find('[BGXWP] {"type":"SESSION"',1,true))
 x.callback()(x.sprite,{m_actionID=3});assert(#x.console==6)
end)
check('no os uses console',function()
 local x=setup({no_os=true});assert(x.module.registered and x.module.writer=='CONSOLE_FALLBACK')
 assert(#x.console==4)
end)
check('io.open denied uses console',function()
 local x=setup({open_fails=true});assert(x.module.registered and x.module.writer=='CONSOLE_FALLBACK')
 x.callback()(x.sprite,{m_actionID=3});assert(x.console[5]:find('"aprRaw":-2',1,true))
end)
check('file write failure falls back and preserves observer',function()
 local x=setup({file_fails=true});assert(x.module.registered)
 x.callback()(x.sprite,{m_actionID=3});assert(x.module.writer=='CONSOLE_FALLBACK' and #x.console>=2)
end)
check('Infinity Log only still works',function()
 local x=setup({no_io=true,no_print=true});assert(x.module.registered and #x.console==2)
end)
check('print only still works',function()
 local x=setup({no_io=true,no_log=true});assert(x.module.registered and #x.console==2)
end)
check('no sink fail closed',function()
 local x=setup({no_io=true,no_log=true,no_print=true});assert(not x.module.registered and not x.callback())
end)
check('no EEex API fail closed',function()
 local x=setup({no_eeex=true});assert(not x.module.registered and not x.callback())
end)
check('non-party ignored',function()
 local x=setup();x.callback()({m_id=99},{m_actionID=3});assert(x.module.recorded==0 and #x.logs==2)
end)
check('bounded 320 actions',function()
 local x=setup();for i=1,325 do x.callback()(x.sprite,{m_actionID=3}) end
 assert(x.module.recorded==320 and x.module.skipped==5)
end)
check('duplicate load does not double register',function()
 local x=setup();local cb=x.callback();assert(loadfile(source,'t',x.env))();assert(x.callback()==cb)
end)
check('no game actions in script',function()
 local s=assert(io.open(source,'rb')):read('*a')
 for _,b in ipairs({'SelectWeaponAbility(', 'ClearActions(', 'Attack(', 'Stop(', 'SetGlobal('}) do
  assert(not s:find(b,1,true),b)
 end
end)
print('R1_1_TESTS '..n..'/16 PASS')
