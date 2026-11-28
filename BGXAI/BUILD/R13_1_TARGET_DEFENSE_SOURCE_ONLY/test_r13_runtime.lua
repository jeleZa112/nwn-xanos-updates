local script='M_BGXTDEF13.lua'
local counter=0
local function T(name,fn)
 local ok,err=pcall(fn)
 if not ok then error('FAILED '..name..': '..tostring(err)) end
 counter=counter+1;print('PASS '..counter..' '..name)
end
local names={'EEex_Action_AddSpriteStartedActionListener','EEex_Sprite_GetInPortraitID','EEex_Sprite_GetActiveStats','EEex_GameObject_Get','Infinity_Log','BGXTargetDefenseR13'}
local old={}
for _,n in ipairs(names)do old[n]=_G[n]end
local priorIO,priorOS=io,os
local logs,listener={},nil
io={open=function()return nil end};os={getenv=function()return nil end}
local item={}
local source={m_id=111,m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,m_items={get=function()return item end}}}
local action={m_actionID=3,m_acteeID={m_Instance=222}}
local target={m_id=222,m_bAllowEffectListCall=1,isSprite=function()return true end}
local defense={m_nArmorClass=-2,m_nACCrushingMod=2,m_nACMissileMod=1,
 m_nACPiercingMod=0,m_nACSlashingMod=-1,
 m_nResistCrushing=20,m_nResistPiercing=0,m_nResistSlashing=15,m_nResistMissile=35}
EEex_Action_AddSpriteStartedActionListener=function(cb) assert(listener==nil);listener=cb end
EEex_Sprite_GetInPortraitID=function(p) return p==0 and 111 or nil end
EEex_Sprite_GetActiveStats=function()return defense end
EEex_GameObject_Get=function(id)return id==222 and target or nil end
Infinity_Log=function(s)logs[#logs+1]=s end
local beforeR4=_G.BGXWeaponActiveR4
local beforeV6=_G.BGXPSTATES
local ok,err=pcall(dofile,script)
T('load requires no game command',function()assert(ok,tostring(err));assert(type(listener)=='function')end)
T('single listener registered',function()assert(BGXTargetDefenseR13.registered==true and BGXTargetDefenseR13.initialized==true)end)
T('session and ready emit',function()assert(#logs==2 and logs[1]:find('"SESSION"') and logs[2]:find('"READY"'))end)
T('normal action logs raw defense',function()
 listener(source,action)
 assert(#logs==3, 'log count='..#logs)
 assert(logs[3]:find('TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY'))
 assert(logs[3]:find('"m_nArmorClass":-2',1,true))
 assert(logs[3]:find('"m_nResistMissile":35',1,true))
 assert(logs[3]:find('"weaponSwitchAuthorized":false',1,true))
end)
T('no EPS commands and R4 unchanged',function()assert(BGXWeaponActiveR4==beforeR4 and BGXPSTATES==beforeV6 and BGXTargetDefenseR13.ordersSent==0)end)
T('nonparty source ignored',function()
 local n=#logs;source.m_id=115;listener(source,action);source.m_id=111;assert(#logs==n)
end)
T('nonattack ignored',function()
 local n=#logs;action.m_actionID=31;listener(source,action);action.m_actionID=3;assert(#logs==n)
end)
T('target changed creates HOLD not action',function()
 action.m_acteeID.m_Instance=444;listener(source,action)
 assert(logs[#logs]:find('"status":"HOLD"'))
 action.m_acteeID.m_Instance=222
end)
T('partial defense logs null',function()
 defense.m_nACMissileMod=nil;listener(source,action)
 assert(logs[#logs]:find('TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY'))
 assert(logs[#logs]:find('"m_nACMissileMod":null',1,true))
 defense.m_nACMissileMod=1
end)
T('changed stats cause HOLD',function()
 local prev=EEex_Sprite_GetActiveStats
 local n=0;EEex_Sprite_GetActiveStats=function() n=n+1;if n%2==0 then defense.m_nArmorClass=-3 else defense.m_nArmorClass=-2 end;return defense end
 listener(source,action);assert(logs[#logs]:find('"status":"HOLD"'))
 EEex_Sprite_GetActiveStats=prev;defense.m_nArmorClass=-2
end)
T('API disappeared is safe HOLD',function()
 local fn=EEex_GameObject_Get;EEex_GameObject_Get=nil
 listener(source,action)
 assert(logs[#logs]:find('"status":"HOLD"'))
 EEex_GameObject_Get=fn
end)
T('event cap 64 never exceeds',function()
 local R=BGXTargetDefenseR13
 for i=1,150 do listener(source,action) end
 assert(R.recorded==64 and R.skipped>0)
end)
T('all JSON events assert no switching',function()
 for _,s in ipairs(logs)do assert(s:find('"weaponSwitchAuthorized":false',1,true),s)end
end)
T('no output fallback commands',function()assert(BGXTargetDefenseR13.errors==0 and BGXTargetDefenseR13.writer=='CONSOLE_FALLBACK')end)
T('missing missile resistance logs null with no dispatch',function()
 defense.m_nResistMissile=nil
 local R=BGXTargetDefenseR13
 R.recorded=10
 listener(source,action)
 assert(logs[#logs]:find('TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY'))
 assert(logs[#logs]:find('"m_nResistMissile":null',1,true))
 assert(logs[#logs]:find('"weaponSwitchAuthorized":false',1,true))
 defense.m_nResistMissile=35
end)
T('real one-round action 105 reuses same listener',function()
 local initial=#logs
 action.m_actionID=105;listener(source,action);action.m_actionID=3
 assert(#logs==initial+1)
 assert(logs[#logs]:find('"rawActionId":105',1,true))
 assert(logs[#logs]:find('TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY'))
 assert(logs[#logs]:find('"dispatchAuthorized":false',1,true))
end)
T('real reevaluate action 134 reuses same listener',function()
 local initial=#logs
 action.m_actionID=134;listener(source,action);action.m_actionID=3
 assert(#logs==initial+1)
 assert(logs[#logs]:find('"rawActionId":134',1,true))
end)
T('temporary target derived stats are HOLD in existing listener',function()
 target.m_bAllowEffectListCall=0
 local initial=#logs
 action.m_actionID=105;listener(source,action);action.m_actionID=3
 target.m_bAllowEffectListCall=1
 assert(#logs==initial+1)
 assert(logs[#logs]:find('"status":"HOLD"',1,true))
 assert(logs[#logs]:find('"dispatchAuthorized":false',1,true))
end)
for _,n in ipairs(names)do _G[n]=old[n]end
io,os=priorIO,priorOS
print(('R13 runtime %d/%d PASS'):format(counter,counter))
