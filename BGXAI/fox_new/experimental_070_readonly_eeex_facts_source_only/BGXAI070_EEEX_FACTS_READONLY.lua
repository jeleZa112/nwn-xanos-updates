-- BGXAI 070 / SOURCE ONLY / NOT INSTALLED.
-- Passive snapshot of known named EEex engine fields. No hooks, I/O, timers,
-- engine orders, local-variable writes, or EPS/BCS changes.
-- Important: A numeric KIT field is NOT a verified kit name; polymorphed != werewolf;
-- levels != proven dual restoration; modal state != an empty or manual action queue.
local M = { version='0.3.37-070-EEEX-NAMED-FIELDS-READONLY-SOURCE-ONLY' }
local MAX_U32=4294967295
local function safe(f)
  local ok, value=pcall(f)
  if ok then return value end
  return nil
end
local function integer(x, max)
  return type(x)=='number' and x==x and x==math.floor(x) and x>=0 and x<=max
end
local function field(s, path)
  return safe(function()
    local v=s
    for i=1,#path do v=v[path[i]] end
    return v
  end)
end
local function non_negative_level(x)
  if integer(x,65535) then return x end
  return nil
end
local function kit_id(x)
  if integer(x,MAX_U32) then return x end
  return nil
end

function M.snapshot(sprite)
  -- Caller passes a real CGameSprite userdata or a read-only test double.
  -- Snapshot's fields are observations, never approvals to take an action.
  local cls=field(sprite,{'m_typeAI','m_Class'})
  if not integer(cls,255) or cls<1 or cls>21 then cls=nil end
  local hp=field(sprite,{'m_baseStats','m_hitPoints'})
  local mh=field(sprite,{'m_derivedStats','m_nMaxHitPoints'})
  local hp_pct=nil
  if type(hp)=='number' and type(mh)=='number' and hp==hp and mh==mh and
     hp>=0 and mh>0 and hp<=mh and mh<10000000 then hp_pct=100*hp/mh end
  local guard=safe(function() return sprite:getLocalInt('BGX38_GUARD') end)
  if guard~=0 and guard~=1 then guard=nil end
  local kit=kit_id(field(sprite,{'m_derivedStats','m_nKit'}))
  -- These named fields exist in published CDerivedStatsTemplate. Their precise
  -- meaning in an altered EET / SCS dual must be checked before use for arbitration.
  local level1=non_negative_level(field(sprite,{'m_derivedStats','m_nLevel1'}))
  local level2=non_negative_level(field(sprite,{'m_derivedStats','m_nLevel2'}))
  local level3=non_negative_level(field(sprite,{'m_derivedStats','m_nLevel3'}))
  local polymorph=field(sprite,{'m_derivedStats','m_bPolymorphed'})
  if polymorph~=0 and polymorph~=1 then polymorph=nil end
  local modal=field(sprite,{'m_nModalState'})
  if not integer(modal,65535) then modal=nil end
  return {
    version=M.version,
    status='RAW_READ_ONLY_NO_VERIFICATION', class_id=cls,
    hp_percent=hp_pct, guard_toggle=guard,
    kit_raw=kit, kit_name='UNKNOWN', kit_verified=false,
    levels={level1,level2,level3}, levels_available={level1~=nil,level2~=nil,level3~=nil},
    polymorph_raw=polymorph, form_name='UNKNOWN', form_verified=false,
    modal_raw=modal, action_queue_verified=false, manual_order_verified=false,
    dual_state='UNKNOWN', dual_verified=false, actual_heal_verified=false,
    combat_eligibility_verified=false, engine_orders_sent=0, hook_registered=false,
  }
end

function M.facts_for_069(snapshot)
  -- NO raw field upgrades itself to an attested semantic fact.
  -- Particularly, the derived-kit integer is NOT KIT.IDS/KITLIST verified,
  -- and any polymorph flag does NOT identify an active werewolf form.
  return {
    kit={verified=false,name='UNKNOWN'},
    form={verified=false,name='UNKNOWN',melee_verified=false},
    -- An absent dual fact remains absent, not a positive unverified-dual claim.
    -- 069's 'UNVERIFIED dual' branch suppresses even base class capabilities.
    dual=nil,
    healing={verified=false,usable_now=false},
    actions={verified=false,manual=nil,casting=nil,singing=nil,
             traps=nil,heal_pending=nil,idle=nil},
    combat={verified=false,same_area=nil,can_act=nil,
            melee=nil,survivability=nil},
  }
end

function M.inspect(sprite, role_observer_069)
  -- Self-contained integration test demonstrating NO action authorization.
  local snapshot=M.snapshot(sprite)
  local result={snapshot=snapshot, role_advice=nil, orders_sent=0}
  if type(role_observer_069)=='table' and type(role_observer_069.inspect)=='function' then
    local advice=safe(function()
      return role_observer_069.inspect(sprite,M.facts_for_069(snapshot))
    end)
    if type(advice)=='table' then result.role_advice=advice end
  end
  return result
end

return M