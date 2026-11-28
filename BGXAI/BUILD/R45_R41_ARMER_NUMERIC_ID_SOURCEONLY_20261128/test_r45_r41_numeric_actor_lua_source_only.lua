-- Real Lua semantics regression only: independent EEex-like Lua wrapper
-- TABLES with equal numeric m_id; no installed game, no engine or BCS calls.
local candidate=assert(arg[1],"R45 alternative Lua file required")
local old=assert(arg[2],"immutable R41 Lua file required")
local checks=0
local function check(label,fn)
 checks=checks+1
 local ok,err=pcall(fn)
 if not ok then error(label..": "..tostring(err)) end
end
local function eq(a,b)assert(a==b,tostring(a).." != "..tostring(b))end
local approval="BGXAI_R41_GUARDED_TYPED_INSTALL_APPROVED"
local keys={F12=1,['Left Ctrl']=2,['Right Ctrl']=3,
            ['Left Alt']=4,['Right Alt']=5,
            ['Left Shift']=6,['Right Shift']=7}
local function fixture(source,opts)
 opts=opts or {}
 local M=assert(loadfile(source))()
 local currentID=1234
 local lv={BGXW3ARM=opts.savedArm or 0,BGXW3TAG=0,BGXW3TRY=0,
           BGXW3QST=0,BGXW3QTM=0,BGXW3MAX=0}
 local callbacks={loaded={},destroyed={},pressed={}}
 local pressed={[2]=true,[4]=true,[6]=true}
 local s={actorId=1234,portraitIndex=1,scriptName='*GCLERIC',
          classRaw=3,kitRaw=16384,strength=12,sourceResref='STAF01',
          sourceSlot=20,targetSlot=35,sourceUnique=true,targetEmpty=true,
          offhandEmpty=true,currentActionIdle=true,queueEmpty=true,
          combatCounter=0,visibleEnemy=false,modalNone=true,
          epsSpellCastCooldownExpired=true,noInterruptionFlags=true,
          itemCurrentShaVerified=true,itemEngineUsable=true,
          activeEffectsChecked=true,partyPortraitSame=true,selectedActorSame=true}
 local ports={preGameStartupVerified=true,runtimeItemUsabilityVerified=true,
              runtimeEffectsVerified=true,scriptOwnerVerified=true,
              manualEpsSafetyVerified=true,
              addLoaded=function(fn)table.insert(callbacks.loaded,fn)end,
              addDestroyed=function(fn)table.insert(callbacks.destroyed,fn)end,
              addPressed=function(fn)table.insert(callbacks.pressed,fn)end,
              getLocal=function(_sprite,key)return lv[key]end,
              setLocal=function(_sprite,key,value)lv[key]=value end,
              getPortraitSprite=function(index)
                eq(index,1)
                return {m_id=currentID} -- fresh Lua wrapper per retrieval
              end,
              keyFromName=function(k)return keys[k]end,
              isDown=function(k)return pressed[k]==true end,
              capture=function()
                local x={}
                for k,v in pairs(s) do x[k]=v end
                if opts.invalidItem then x.itemEngineUsable=nil end
                if opts.invalidAction then x.queueEmpty=false end
                return x
              end}
 local result=M.prepare(ports,approval)
 eq(result.status,'R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 local f={module=M,lv=lv,callbacks=callbacks,snapshot=s,
  loaded=function() for _,fn in ipairs(callbacks.loaded) do fn({m_id=currentID}) end end,
  destroy=function()for _,fn in ipairs(callbacks.destroyed) do fn() end end,
  changeID=function(id)currentID=id end,
  request=function()
    if #callbacks.pressed~=1 then return false end
    return callbacks.pressed[1](1,false)
  end,
  gate=function(id)
    _G.EEex_LuaTrigger_Object={m_id=id or currentID} -- independent wrapper
    local global=_G.BGXW3_EEexSessionGate
    local value=type(global)=='function' and global() or false
    _G.EEex_LuaTrigger_Object=nil
    return value
  end}
 return f
end
local function cleanup()
 _G.EEex_LuaTrigger_Object=nil
 _G.BGXW3_EEexSessionGate=nil
end

check("original R41 wrongly refuses same-id newly wrapped sprite",function()
 cleanup()
 local f=fixture(old)
 f.loaded()
 eq(#f.callbacks.pressed,0)
 eq(f.module.registered,false)
 cleanup()
end)
check("R45 R41 binds keyboard for same actor despite new wrapper",function()
 cleanup()
 local f=fixture(candidate)
 f.loaded()
 eq(#f.callbacks.pressed,1)
 eq(f.module.registered,true)
 eq(f.lv.BGXW3ARM,0)
 eq(f.module.ordersSent,0)
 cleanup()
end)
check("R45 fresh Lua trigger wrapper same-id passes only after explicit key",function()
 cleanup()
 local f=fixture(candidate)
 f.loaded()
 eq(f.gate(1234),false) -- no gesture, no saved ARM
 eq(f.request(),true)
 eq(f.lv.BGXW3ARM,1)
 eq(f.gate(1234),true) -- mocked proofs, not real live authorization
 eq(f.module.ordersSent,0)
 cleanup()
end)
check("R45 rejects trigger object different numeric m_id",function()
 cleanup()
 local f=fixture(candidate)
 f.loaded();eq(f.request(),true)
 eq(f.gate(1235),false)
 cleanup()
end)
check("R45 rejects current portrait changed after gesture",function()
 cleanup()
 local f=fixture(candidate)
 f.loaded();eq(f.request(),true)
 f.changeID(5678)
 eq(f.gate(1234),false)
 cleanup()
end)
check("R45 refuses to bind wrong actor loaded",function()
 cleanup()
 local f=fixture(candidate)
 f.changeID(5678)
 f.loaded() -- real portrait differs from snapshot? Load uses same changed numeric id
 -- Loaded actor is numerically 5678 and snapshot is Jagan 1234.
 -- R41 may bind keyboard as load confirms portrait, but R39 snapshot refuses arming.
 eq(f.request(),true)
 eq(f.lv.BGXW3ARM,0)
 eq(f.gate(5678),false)
 cleanup()
end)
check("R45 invalid item usability cannot arm even with same actor",function()
 cleanup()
 local f=fixture(candidate,{invalidItem=true})
 f.loaded();eq(f.request(),true)
 eq(f.lv.BGXW3ARM,0);eq(f.gate(1234),false)
 cleanup()
end)
check("R45 nonempty action queue cannot arm",function()
 cleanup()
 local f=fixture(candidate,{invalidAction=true})
 f.loaded();eq(f.request(),true)
 eq(f.lv.BGXW3ARM,0);eq(f.gate(1234),false)
 cleanup()
end)
check("R45 R40 clears saved ARM before new actor binding",function()
 cleanup()
 local f=fixture(candidate,{savedArm=1})
 f.loaded()
 eq(f.lv.BGXW3ARM,0)
 eq(f.gate(1234),false)
 cleanup()
end)
check("R45 R40 game destroyed epoch invalidates volatile arm",function()
 cleanup()
 local f=fixture(candidate)
 f.loaded();eq(f.request(),true);eq(f.gate(1234),true)
 f.destroy()
 eq(f.gate(1234),false)
 cleanup()
end)
check("R45 remains inert without approved R41 prepare",function()
 cleanup()
 local M=assert(loadfile(candidate))()
 eq(M.registered,false)
 eq(M.ordersSent,0)
 eq(_G.BGXW3_EEexSessionGate,nil)
 cleanup()
end)
print("BGXAI R45 WRAPPER ID SOURCE ONLY "..checks.."/"..checks..
      " PASS; GAME NOT TOUCHED; XEquip NOT EXECUTED")
