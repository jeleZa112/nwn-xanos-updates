#include "uai_core"

void UAI_DoMelee(object oTarget, int nHP)
{
    if (!UAI_EquipMelee(oTarget))
    {
        UAI_Fallback();
        return;
    }

    if (GetHasFeat(FEAT_EXPERTISE, OBJECT_SELF))
    {
        int bExp = nHP <= 35;
        if (GetActionMode(OBJECT_SELF, ACTION_MODE_EXPERTISE) != bExp)
            SetActionMode(OBJECT_SELF, ACTION_MODE_EXPERTISE, bExp);
    }

    if (GetHasFeat(FEAT_POWER_ATTACK, OBJECT_SELF))
    {
        int bPA = nHP > 45 &&
                  GetAC(oTarget) <= GetBaseAttackBonus(OBJECT_SELF) +
                  UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_STRENGTH)) + 8;
        if (GetActionMode(OBJECT_SELF, ACTION_MODE_POWER_ATTACK) != bPA)
            SetActionMode(OBJECT_SELF, ACTION_MODE_POWER_ATTACK, bPA);
    }

    if (!UAI_TryManeuver(oTarget, FALSE)) ActionAttack(oTarget);
    SetLocalString(OBJECT_SELF, "UAI_LAST_ACTION", "MELEE");
    SetLocalInt(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT_OK", TRUE);
}

void UAI_DoRanged(object oTarget)
{
    if (!UAI_EquipRanged(oTarget))
    {
        UAI_DoMelee(oTarget, UAI_HPPercent(OBJECT_SELF));
        return;
    }

    if (GetHasFeat(FEAT_RAPID_SHOT, OBJECT_SELF))
    {
        int bRapid = GetAC(oTarget) <= GetBaseAttackBonus(OBJECT_SELF) +
                     UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_DEXTERITY)) + 10;
        if (GetActionMode(OBJECT_SELF, ACTION_MODE_RAPID_SHOT) != bRapid)
            SetActionMode(OBJECT_SELF, ACTION_MODE_RAPID_SHOT, bRapid);
    }

    if (!UAI_TryManeuver(oTarget, TRUE)) ActionAttack(oTarget);
    SetLocalString(OBJECT_SELF, "UAI_LAST_ACTION", "RANGED");
    SetLocalInt(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT_OK", TRUE);
}

void main()
{
    if (!GetLocalInt(OBJECT_SELF, UAI_MARK) || GetLocalInt(OBJECT_SELF, "AI_TURNED_OFF"))
    {
        UAI_Fallback();
        return;
    }

    // If this creature is no longer owned by the PC that UAI attached to,
    // stop wrapping its AI rather than leaving a stale companion controller behind.
    object oSavedMaster = GetLocalObject(OBJECT_SELF, UAI_MASTER);
    object oRealMaster = GetMaster(OBJECT_SELF);
    if (!GetIsObjectValid(oSavedMaster) || !GetIsPC(oSavedMaster) ||
        (GetIsObjectValid(oRealMaster) && oRealMaster != oSavedMaster))
    {
        UAI_DetachAndFallback();
        return;
    }

    int nTick = GetLocalInt(OBJECT_SELF, UAI_TICK) + 1;
    SetLocalInt(OBJECT_SELF, UAI_TICK, nTick);

    object oTarget = UAI_SelectTarget();
    if (!GetIsObjectValid(oTarget))
    {
        UAI_Fallback();
        return;
    }

    UAI_Profile(OBJECT_SELF);
    UAI_AdaptArmor(oTarget);

    string sRole = GetLocalString(OBJECT_SELF, UAI_ROLE);
    float fDist = GetDistanceBetween(OBJECT_SELF, oTarget);
    int nHP = UAI_HPPercent(OBJECT_SELF);
    int bWeak = UAI_IsWeakTarget(oTarget);

    // Universal resource economy: obvious weak non-casters are weapon work,
    // even for a spellcaster. This mirrors the proven Xanos 0.7.10.7 policy.
    if (bWeak)
    {
        if (fDist <= 4.5)
        {
            UAI_DoMelee(oTarget, nHP);
            SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "ECONOMY_CLOSE");
            return;
        }

        if (UAI_HasRangedInventory(OBJECT_SELF))
        {
            UAI_DoRanged(oTarget);
            SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "ECONOMY_RANGED");
            return;
        }

        UAI_DoMelee(oTarget, nHP);
        SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "ECONOMY_CHASE");
        return;
    }

    // Hard targets: true casters/healers keep the module/PRC spell AI.
    // UAI does not pretend to understand every PRC spellbook yet.
    if (sRole == "CASTER" || sRole == "HEALER")
    {
        SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "CASTER_FALLBACK");
        UAI_Fallback();
        return;
    }

    if (fDist <= 4.5)
    {
        UAI_DoMelee(oTarget, nHP);
        SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "CLOSE_MELEE");
        return;
    }

    if (sRole == "RANGED" || sRole == "UTILITY_RANGED" || sRole == "HYBRID")
    {
        UAI_DoRanged(oTarget);
        SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "RANGED");
        return;
    }

    if (sRole == "MELEE" || sRole == "UTILITY")
    {
        UAI_DoMelee(oTarget, nHP);
        SetLocalString(OBJECT_SELF, "UAI_LAST_POLICY", "MELEE_CHASE");
        return;
    }

    UAI_Fallback();
}
