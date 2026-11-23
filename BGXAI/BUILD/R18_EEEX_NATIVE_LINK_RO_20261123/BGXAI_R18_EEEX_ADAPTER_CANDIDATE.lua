-- BGXAI R18: on-demand native EEex v1.1.7 source API ADAPTER CANDIDATE.
-- NOT INSTALLED. Requires audit of matching EEex in the user's build before use.
-- No startup hook, no registration, no game writes, no effect-list traversal.
local A={version='BGXAI_R18_EEEX_ADAPTER_SOURCE_ONLY', installed=false}
local function read(f)
 local ok,v=pcall(f)
 if ok then return v end
 return nil
end
local function ref(item)
 if item==nil then return nil end
 local x=read(function() return item.cResRef:get() end)
 if type(x)=='string' and #x>=1 and #x<=8 and not x:find('[^%w_]') then
  return x:upper()
 end
 return nil
end
function A.read_event(sprite,action)
 return {actor=read(function()return sprite.m_id end),
  target=read(function()return action.m_acteeID.m_Instance end),
  action=read(function()return action.m_actionID end)}
end
function A.read_selection(sprite)
 local eq=read(function()return sprite.m_equipment end)
 if eq==nil then return nil end
 local slot=read(function()return eq.m_selectedWeapon end)
 local index=read(function()return eq.m_selectedWeaponAbility end)
 if type(slot)~='number' or slot%1~=0 or slot<10 or slot>38 then return nil end
 if type(index)~='number' or index%1~=0 or index<0 or index>31 then return nil end
 if slot==10 then return {slot=slot,abilityIndex=index,resref=nil} end
 local item=read(function()return eq.m_items:get(slot) end)
 return {slot=slot,abilityIndex=index,resref=ref(item)}
end
function A.read_ability(sprite,selection)
 if type(selection)~='table' or selection.slot==10 then return nil end
 local eq=read(function()return sprite.m_equipment end)
 local item=eq and read(function()return eq.m_items:get(selection.slot) end)
 if item==nil or ref(item)~=selection.resref then return nil end
 -- Confirmed upstream EEex v1.1.7 helper name: CItem.getAbility.
 -- Do NOT dereference Item_ability_st fields or log raw pointers here.
 local ability=read(function()return item:getAbility(selection.abilityIndex) end)
 if ability==nil then return nil end
 return {present=true,handle=ability} -- Handle is only passed locally, never serialized.
end
function A.read_launcher(sprite,selection,ability)
 if type(selection)~='table' or type(ability)~='table' or ability.handle==nil then return nil end
 -- Upstream EEex_Sprite_GetLauncher(sprite, Item_ability_st) returns
 -- CItem launcher and inventory slot. Unverified in the installed EEex bytes.
 local ok,item,slot=pcall(function()return sprite:getLauncher(ability.handle) end)
 if not ok or item==nil or type(slot)~='number' then return nil end
 return {slot=slot,resref=ref(item)}
end
local KEYS={
 'm_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nDEX',
 'm_nMeleeTHAC0Bonus','m_nMissileTHAC0Bonus','m_bImprovedHaste','m_nLuck'
}
function A.read_stats(sprite)
 if type(EEex_Sprite_GetActiveStats)~='function' then return nil end
 local st=read(function()return EEex_Sprite_GetActiveStats(sprite) end)
 if st==nil then return nil end
 local fields={}
 for _,key in ipairs(KEYS) do
  local value=read(function()return st[key] end)
  if value==nil then return nil end
  fields[key]=value
 end
 return fields
end
return A
