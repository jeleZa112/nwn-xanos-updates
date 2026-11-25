-- BGXAI R32: mocks of documented EEex C2DArray, no game loader in tests.
local root=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(root..'BGXAI_R32_EEEX_ENGINE_2DA_RO.lua')
local function eq(a,b)assert(a==b,tostring(a)..' != '..tostring(b))end
local count=0
local function test(label,fn)fn();count=count+1;print('PASS '..label)end
local function make(columns,rows)
 return {
  getDimensions=function()return #columns+1,#rows end,
  getColumnLabel=function(_,index)return columns[index+1]end,
  getRowLabel=function(_,index)return rows[index+1].label end,
  getAtPoint=function(_,x,y)return rows[y+1].cells[x+1]end
 }
end
local function sample()
 local columns={'LEVEL1'}
 for i=2,40 do columns[#columns+1]=tostring(i)end
 local wspRows={}
 for rank=0,5 do
  local cells={}
  for level=1,40 do
   local v
   if rank<2 then
    v=(level<7) and 0 or (level<13 and -1 or 1)
   else
    v=(level<7) and -1 or (level<13 and 1 or -2)
   end
   cells[level]=tostring(v)
  end
  wspRows[#wspRows+1]={label=tostring(rank),cells=cells}
 end
 return {
  WSPATCK=make(columns,wspRows),
  CLSWPBON=make({'GETS_PROF_APR','UNARMED_DIVISOR','ZERO_SKILL_THAC0'},{
   {label='FIGHTER',cells={'1','0','2'}},
   {label='THIEF',cells={'0','0','3'}},
   {label='MONK',cells={'1','3','2'}},
   {label='FIGHTER_MAGE',cells={'1','0','2'}},
  }),
 }
end
local function source(data)
 return function(resref)return data[resref]end
end
test('real format R32 engine 2DA lvl1 2 pips +0.5 not final APR',function()
 local r=M.observe('FIGHTER',2,1,source(sample()))
 eq(r.status,'ENGINE_RESOLVED_APR_TABLE_CANDIDATE_READ_ONLY')
 eq(r.wspatckRawValue,-1)
 eq(r.tableBonusAPRIfActorClassVerified,0.5)
 eq(r.finalAPR,nil)
 eq(r.engineFinalAPRVerified,false)
 eq(r.otherSlotEffectiveAPRVerified,false)
 eq(r.dispatchAuthorized,false)
 eq(r.weaponSwitchAuthorized,false)
end)
test('level 7 +1 and level 13 +1.5 APR bonus, no second addition',function()
 for _,q in ipairs({{7,1,1},{13,-2,1.5}})do
  local r=M.observe('FIGHTER',2,q[1],source(sample()))
  eq(r.wspatckRawValue,q[2]);eq(r.tableBonusAPRIfActorClassVerified,q[3])
  eq(r.tableBonusIsAdditiveNotFinalAPR,true)
 end
end)
test('THIEF does not get proficiency APR even though WSPATCK has value',function()
 local r=M.observe('THIEF',2,13,source(sample()))
 eq(r.getsProfAprTableFlag,false)
 eq(r.wspatckRawValue,-2)
 eq(r.tableBonusAPRIfActorClassVerified,0)
end)
test('multiclass source row does not prove active class or kit',function()
 local r=M.observe('FIGHTER_MAGE',2,1,source(sample()))
 eq(r.status,'ENGINE_RESOLVED_APR_TABLE_CANDIDATE_READ_ONLY')
 eq(r.activeDualMultiClassVerified,false)
 eq(r.proficiencyGroupVerified,false)
end)
test('MONK unarmed divisor not confused with WSPATCK bonus',function()
 local r=M.observe('MONK',2,1,source(sample()))
 eq(r.tableBonusAPRIfActorClassVerified,0.5)
 eq(r.gameplayWeaponPriorityVerified,false)
end)
test('missing WSPATCK or CLSWPBON return HOLD; no BIF guesses',function()
 for _,key in ipairs({'WSPATCK','CLSWPBON'})do
  local data=sample();data[key]=nil
  local r=M.observe('FIGHTER',2,1,source(data))
  eq(r.status,'HOLD_ENGINE_APR_TABLE_SOURCE_UNVERIFIED')
  eq(r.ordersSent,0);eq(r.engineResourcesRead,false)
 end
end)
test('missing EEex API return HOLD',function()
 local saved=EEex_Resource_Load2DA
 EEex_Resource_Load2DA=nil
 local r=M.observe('FIGHTER',2,1)
 EEex_Resource_Load2DA=saved
 eq(r.reason,'EEEX_LOAD2DA_API_UNAVAILABLE')
end)
test('EEex loader throws safely',function()
 local r=M.observe('FIGHTER',2,1,function()error('resource failed')end)
 eq(r.reason,'LOAD2DA_MISSING_WSPATCK')
end)
test('malformed row width never silently uses defaults',function()
 local data=sample();data.WSPATCK.getAtPoint=function()return nil end
 local r=M.observe('FIGHTER',2,1,source(data))
 eq(r.reason,'MISSING_OR_BAD_CELL_WSPATCK')
end)
test('non-integer WSPATCK values fail',function()
 for _,bad in ipairs({'1.5','*','UNKNOWN'})do
  local data=sample()
  local original=data.WSPATCK.getAtPoint
  data.WSPATCK.getAtPoint=function(self,x,y)
   if x==0 and y==2 then return bad end
   return original(self,x,y)
  end
  local r=M.observe('FIGHTER',2,1,source(data))
  eq(r.reason,'WSPATCK_BAD_CELL')
 end
end)
test('CLSWPBON value 2 not allowed',function()
 local data=sample()
 local f=data.CLSWPBON.getAtPoint
 data.CLSWPBON.getAtPoint=function(self,x,y)
  if x==0 and y==0 then return '2' end
  return f(self,x,y)
 end
 local r=M.observe('FIGHTER',2,1,source(data))
 assert(r.reason:match('CLSWPBON_INVALID_FLAG'))
end)
test('invalid dimension or C2DArray getter throws',function()
 local d=sample();d.WSPATCK.getDimensions=function()return 2000000,1000000 end
 eq(M.observe('FIGHTER',2,1,source(d)).reason,'BAD_DIMENSIONS_WSPATCK')
 local t=sample();t.CLSWPBON.getDimensions=function()error('broken')end
 eq(M.observe('FIGHTER',2,1,source(t)).reason,'BAD_DIMENSIONS_CLSWPBON')
end)
test('duplicate labels fail closed',function()
 local t=sample()
 t.CLSWPBON.getRowLabel=function(_,index)
  if index==1 then return 'FIGHTER' end
  return ({'FIGHTER','THIEF','MONK','FIGHTER_MAGE'})[index+1]
 end
 eq(M.observe('FIGHTER',2,1,source(t)).reason,'DUPLICATE_ROW_CLSWPBON')
end)
test('out of bounds level and unknown class are explicit holds',function()
 local loader=source(sample())
 eq(M.observe('FIGHTER',2,41,loader).reason,'LEVEL_NOT_PRESENT')
 eq(M.observe('FIGHTER_THIEF',2,1,loader).reason,'CLASS_ROW_NOT_PRESENT')
end)
test('query rank range enforced and false cannot mean 0',function()
 local loader=source(sample())
 for _,v in ipairs({-1,6,2.5,false})do
  eq(M.observe('FIGHTER',v,1,loader).reason,'QUERY_INVALID')
 end
end)
test('no false approval with unknown class origin even if engine resolved',function()
 local data=sample()
 local r=M.observe('FIGHTER',2,1,source(data))
 eq(r.engineResourcesRead,true)
 eq(r.engineResourceVersionAuthenticated,false)
 eq(r.allLiveEffectsObserved,false)
 eq(r.ordersSent,0);eq(r.localsWritten,0)
 eq(r.actionQueueCleared,false);eq(r.currentActionPreserved,true)
end)
test('WSPATCK duplicate level label and missing rank are holds',function()
 local d=sample()
 d.WSPATCK.getColumnLabel=function(_,x)
  if x==1 then return 'LEVEL1' end
  return x==0 and 'LEVEL1' or tostring(x+1)
 end
 eq(M.observe('FIGHTER',2,1,source(d)).reason,'DUPLICATE_COLUMN_WSPATCK')
 local t=sample()
 t.WSPATCK.getRowLabel=function(_,y) return y==2 and '7' or tostring(y) end
 eq(M.observe('FIGHTER',2,1,source(t)).reason,'WSPATCK_MISSING_RANK')
end)
print('PASS R32 EEEX C2DARRAY RESOURCE READER '..count..'/'..count..' SOURCE ONLY')
