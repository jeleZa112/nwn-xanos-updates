-- Validates an ALTERNATIVE SOURCE-ONLY R39 patch against its exact predecessor.
-- No EEex, EET game, engine actions, or listener is executed.
local candidatePath=assert(arg[1],"candidate Lua required")
local oldPath=assert(arg[2],"original Lua required")
local new=assert(loadfile(candidatePath))()
local old=assert(loadfile(oldPath))()
local total=0
local function test(label,fn)
 total=total+1
 local ok,err=pcall(fn)
 if not ok then error(label..": "..tostring(err)) end
end
local function eq(a,b)assert(a==b,tostring(a).." != "..tostring(b))end
local SCRIPT_LEVELS={[0]="C#GREY",[1]="",[2]="",[4]="BDDEFAI",
                     [5]="",[6]="",[7]="DPLAYER3"}
local function setup(opts)
 opts=opts or {}
 local stored={m_id=1002,kit=16384,str=12,class=3,selected={1002},
               items={},scripts={}}
 for level,name in pairs(SCRIPT_LEVELS) do stored.scripts[level]=name end
 stored.items[20]={cResRef={get=function()return "STAF01" end},
                   m_flags=1,m_useCount1=0,m_useCount2=0,m_useCount3=0}
 local countSprite=0
 local countIDs=0
 local readCount=0
 local function wrapper()
   -- Different Lua TABLES, same actual engine actor ID / underlying inventory.
   return {m_id=stored.m_id,m_typeAI={m_Class=stored.class},
           m_equipment={m_items={get=function(_,k)return stored.items[k] end}},
           getActiveStats=function() return {m_nKit=stored.kit,m_nSTR=stored.str} end,
           m_curScriptNum=-1,m_curAction={m_actionID=23}}
 end
 local p={}
 p.getPortraitSprite=function()
   countSprite=countSprite+1
   if opts.changeActorId and countSprite==2 then stored.m_id=1003 end
   return wrapper()
 end
 p.getPortraitID=function()
   countIDs=countIDs+1
   if opts.changePortraitOnly and countIDs==2 then return 1003 end
   return stored.m_id
 end
 p.getSelectedIDs=function()
   if opts.changeSelected and countSprite>=2 then return {1003} end
   return stored.selected
 end
 p.getScriptLevelResRef=function(sprite,level)
   readCount=readCount+1
   if opts.changeInventory and readCount==8 then
     stored.items[35]={cResRef={get=function() return "STAF01" end},
         m_flags=1,m_useCount1=0,m_useCount2=0,m_useCount3=0}
   end
   if opts.changeScript and readCount>7 and level==4 then return "PRIEST1" end
   if opts.unreadable then return "VERY_LONG_SCRIPT" end
   return stored.scripts[level]
 end
 return p
end
local function no_orders(r)
 eq(r.ordersSent,0);eq(r.localsWritten,0)
 eq(r.armAuthorized,false);eq(r.dispatchAuthorized,false)
 eq(r.canArm,false);eq(r.gameModified,false)
end

test("old comparison FALSE-HOLD for same id but fresh wrappers",function()
 local r=old.probeScriptAssignments(setup())
 eq(r.status,"HOLD_SCRIPT_ACTOR_CHANGED")
 no_orders(r)
end)
test("new comparison accepts separate wrappers sharing engine numeric ID",function()
 local r=new.probeScriptAssignments(setup())
 eq(r.status,"R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY")
 eq(r.scriptLevelResrefs[4],"BDDEFAI")
 eq(r.pilotPhysicalSnapshotDoubleMatched,true)
 eq(r.actualBcsExecutionVerified,false)
 eq(r.scriptSlotOwnershipVerified,false)
 no_orders(r)
end)
test("actual actor ID change still HOLD",function()
 local r=new.probeScriptAssignments(setup({changeActorId=true}))
 eq(r.status,"HOLD_SCRIPT_ACTOR_CHANGED");no_orders(r)
end)
test("portrait ID changes while sprite stays HOLD",function()
 local r=new.probeScriptAssignments(setup({changePortraitOnly=true}))
 eq(r.status,"HOLD_SCRIPT_ACTOR_CHANGED");no_orders(r)
end)
test("second selection differs still HOLD",function()
 local r=new.probeScriptAssignments(setup({changeSelected=true}))
 eq(r.status,"HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED")
 eq(r.reason,"HOLD_SELECTION_NOT_EXACTLY_THIS_ACTOR")
 no_orders(r)
end)
test("inventory changes after first seven resrefs still HOLD",function()
 local r=new.probeScriptAssignments(setup({changeInventory=true}))
 eq(r.status,"HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED")
 no_orders(r)
end)
test("script resref changes between reads still HOLD",function()
 local r=new.probeScriptAssignments(setup({changeScript=true}))
 eq(r.status,"HOLD_SCRIPT_RESREF_CHANGED");no_orders(r)
end)
test("malformed assigned resref still HOLD",function()
 local r=new.probeScriptAssignments(setup({unreadable=true}))
 eq(r.status,"HOLD_SCRIPT_RESREF_UNREADABLE");no_orders(r)
end)
test("original and alternative remain source-only",function()
 eq(new.registered,false);eq(new.sourceOnly,true);eq(new.ordersSent,0)
 eq(old.registered,false);eq(old.sourceOnly,true)
end)
print("BGXAI R39 ACTOR_ID_WRAPPER SOURCE ONLY "..total.."/"..total.." PASS; GAME NOT TOUCHED")
