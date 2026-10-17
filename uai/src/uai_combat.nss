#include "uai_core"

void main()
{
    if (!GetLocalInt(OBJECT_SELF, UAI_MARK) || GetLocalInt(OBJECT_SELF, "AI_TURNED_OFF"))
    {
        UAI_Fallback();
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

    // Pure casters/healers keep their existing PRC/vanilla spell AI at range.
    // UAI still scans their live gear/capabilities and can protect them in close melee.
    if ((sRole == "CASTER" || sRole == "HEALER") && fDist > 4.5)
    {
        UAI_Fallback();
        return;
    }

    if (fDist <= 4.5)
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
            int bPA = nHP > 45 && GetAC(oTarget) <= GetBaseAttackBonus(OBJECT_SELF) + UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_STRENGTH)) + 8;
            if (GetActionMode(OBJECT_SELF, ACTION_MODE_POWER_ATTACK) != bPA)
                SetActionMode(OBJECT_SELF, ACTION_MODE_POWER_ATTACK, bPA);
        }

        if (!UAI_TryManeuver(oTarget, FALSE)) ActionAttack(oTarget);
        SetLocalString(OBJECT_SELF, "UAI_LAST_ACTION", "MELEE");
        SetLocalInt(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT_OK", TRUE);
        return;
    }

    if ((sRole == "RANGED" || sRole == "UTILITY_RANGED" || sRole == "HYBRID") && UAI_EquipRanged(oTarget))
    {
        if (GetHasFeat(FEAT_RAPID_SHOT, OBJECT_SELF))
        {
            int bRapid = GetAC(oTarget) <= GetBaseAttackBonus(OBJECT_SELF) + UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_DEXTERITY)) + 10;
            if (GetActionMode(OBJECT_SELF, ACTION_MODE_RAPID_SHOT) != bRapid)
                SetActionMode(OBJECT_SELF, ACTION_MODE_RAPID_SHOT, bRapid);
        }
        if (!UAI_TryManeuver(oTarget, TRUE)) ActionAttack(oTarget);
        SetLocalString(OBJECT_SELF, "UAI_LAST_ACTION", "RANGED");
        SetLocalInt(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT_OK", TRUE);
        return;
    }

    if (sRole == "MELEE" || sRole == "UTILITY")
    {
        if (UAI_EquipMelee(oTarget))
        {
            ActionAttack(oTarget);
            SetLocalString(OBJECT_SELF, "UAI_LAST_ACTION", "MELEE_CHASE");
            SetLocalInt(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT_OK", TRUE);
            return;
        }
    }

    UAI_Fallback();
}
