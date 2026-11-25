-- BGXAI R32: candidate read of engine-resolved WSPATCK / CLSWPBON through EEex.
-- SOURCE ONLY: no hooks, orders, BCS/LOCALS, item equip, stat writes, GC frees.
-- API basis: Bubb13 EEex_Resource.lua Load2DA/getDimensions/getColumnLabel/
-- getRowLabel/getAtPoint, 0-based indices; sizeX INCLUDES row-label column.
-- This never proves class/kit/dual identity or effective alternate weapon APR.
local M={version='BGXAI_R32_EEEX_ENGINE_2DA_RO_V1',installed=false}
local function integer(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function name(x)
 return type(x)=='string' and #x>=1 and #x<=80 and
        not x:upper():find('[^A-Z0-9_]')
end
local function safe(f)
 local ok,a,b=pcall(f)
 if not ok then return nil,nil end
 return a,b
end
local function out(status,reason)
 return {schema='BGXAI_R32_EEEX_ENGINE_2DA_RO_V1',
  status=status,reason=reason,installed=false,readOnly=true,
  engineResourcesRead=false,engineResourceVersionAuthenticated=false,
  allLiveEffectsObserved=false,engineFinalAPRVerified=false,
  otherSlotEffectiveAPRVerified=false,activeDualMultiClassVerified=false,
  proficiencyGroupVerified=false,gameplayWeaponPriorityVerified=false,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,ordersSent=0,
  localsWritten=0,actionQueueCleared=false,currentActionPreserved=true}
end
local function hold(reason)
 return out('HOLD_ENGINE_APR_TABLE_SOURCE_UNVERIFIED',reason)
end
local function read_array(loader,resref,maxCols,maxRows)
 local array=safe(function()return loader(resref)end)
 if array==nil then return nil,'LOAD2DA_MISSING_'..resref end
 -- Never call .free() on EEex Load2DA result; EEex provides managed GC.
 local sizeX,sizeY=safe(function()return array:getDimensions()end)
 if not integer(sizeX,2,maxCols+1) or not integer(sizeY,1,maxRows) then
  return nil,'BAD_DIMENSIONS_'..resref end
 local columns,rows={},{}
 for x=0,sizeX-2 do
  local col=safe(function()return array:getColumnLabel(x)end)
  if not name(col) then return nil,'BAD_COLUMN_'..resref end
  col=col:upper()
  if columns[col]~=nil then return nil,'DUPLICATE_COLUMN_'..resref end
  columns[col]=x
 end
 local rowKeys={}
 for y=0,sizeY-1 do
  local key=safe(function()return array:getRowLabel(y)end)
  if not name(key) then return nil,'BAD_ROW_'..resref end
  key=key:upper()
  if rows[key]~=nil then return nil,'DUPLICATE_ROW_'..resref end
  rowKeys[#rowKeys+1]=key
  local cells={}
  for x=0,sizeX-2 do
   local value=safe(function()return array:getAtPoint(x,y)end)
   if type(value)~='string' or #value<1 or #value>40 then
    return nil,'MISSING_OR_BAD_CELL_'..resref end
   cells[x]=value
  end
  rows[key]=cells
 end
 return {columns=columns,rows=rows,numberColumns=sizeX-1,
  numberRows=sizeY,rowKeys=rowKeys},nil
end
local function number(raw,lo,hi)
 if type(raw)~='string' or not raw:match('^%-?%d+$') then return nil end
 local n=tonumber(raw)
 if integer(n,lo,hi) then return n end
 return nil
end
local function bonus(encoded)
 return encoded>=0 and encoded or -encoded-0.5
end
function M.observe(classRow,rank,level,loader)
 if not name(classRow) or not integer(rank,0,5) or
    not integer(level,1,50) then return hold('QUERY_INVALID') end
 if loader==nil then loader=EEex_Resource_Load2DA end
 if type(loader)~='function' then return hold('EEEX_LOAD2DA_API_UNAVAILABLE') end
 local wsp,err=read_array(loader,'WSPATCK',50,6)
 if not wsp then return hold(err) end
 local cls,why=read_array(loader,'CLSWPBON',32,200)
 if not cls then return hold(why) end
 if wsp.numberRows~=6 or wsp.numberColumns<1 or wsp.numberColumns>50 then
  return hold('WSPATCK_STRUCTURE_INVALID') end
 local levelCol
 for label,x in pairs(wsp.columns) do
  local n=label:match('^LEVEL(%d+)$') or label:match('^(%d+)$')
  if not n then return hold('WSPATCK_LEVEL_LABEL_INVALID') end
  n=tonumber(n)
  if not integer(n,1,50) or n~=x+1 then
   return hold('WSPATCK_LEVEL_ORDER_INVALID') end
  if n==level then levelCol=x end
 end
 for pip=0,5 do
  local row=wsp.rows[tostring(pip)]
  if row==nil then return hold('WSPATCK_MISSING_RANK') end
  for x=0,wsp.numberColumns-1 do
   if number(row[x],-10,10)==nil then return hold('WSPATCK_BAD_CELL') end
  end
 end
 for key in pairs(wsp.rows) do
  local p=tonumber(key)
  if not integer(p,0,5) then return hold('WSPATCK_EXTRA_RANK') end
 end
 local flagCol=cls.columns['GETS_PROF_APR']
 if flagCol==nil or cls.columns['UNARMED_DIVISOR']==nil or
    cls.columns['ZERO_SKILL_THAC0']==nil then
  return hold('CLSWPBON_REQUIRED_COLUMNS_MISSING') end
 for row,cells in pairs(cls.rows) do
  local flag=number(cells[flagCol],0,1)
  if flag==nil then return hold('CLSWPBON_INVALID_FLAG_'..row) end
 end
 classRow=classRow:upper()
 local class=cls.rows[classRow]
 if class==nil then return hold('CLASS_ROW_NOT_PRESENT') end
 if levelCol==nil then return hold('LEVEL_NOT_PRESENT') end
 local raw=number(wsp.rows[tostring(rank)][levelCol],-10,10)
 local flag=number(class[flagCol],0,1)
 if raw==nil or flag==nil then return hold('ROW_VALUE_INVALID') end
 local result=out('ENGINE_RESOLVED_APR_TABLE_CANDIDATE_READ_ONLY')
 result.engineResourcesRead=true
 result.tableReadMethod='EEEX_RESOURCE_LOAD2DA_C2DARRAY'
 result.engineResourceVersionAuthenticated=false
 result.classRowUnverified=classRow
 result.proficiencyRankUnverified=rank
 result.classLevelUnverified=level
 result.wspatckColumnCount=wsp.numberColumns
 result.wspatckRowCount=wsp.numberRows
 result.clswpbonRowCount=cls.numberRows
 result.getsProfAprTableFlag=(flag==1)
 result.wspatckRawValue=raw
 result.tableBonusAPRIfActorClassVerified=(flag==1) and bonus(raw) or 0
 result.tableBonusIsAdditiveNotFinalAPR=true
 result.finalAPR=nil
 return result
end
return M
