#include "uai_core"

int UAI_UtilitySpellReady(int nSpell)
{
    int i;
    for (i = 1; i <= 3; i++)
    {
        int nClass = GetClassByPosition(i, OBJECT_SELF);
        if (nClass == CLASS_TYPE_INVALID) continue;
        if (GetSpellUsesLeft(OBJECT_SELF, nClass, nSpell) > 0) return TRUE;
    }
    return FALSE;
}

int UAI_UtilityPotentialBuff(int nSkill)
{
    int n = 0;

    // Only engine-stable ability buffs are used in the first universal build.
    // PRC/non-stock spell packages remain fallback territory until their spell IDs
    // are discovered from the actual installed ruleset rather than guessed.
    if (nSkill == SKILL_OPEN_LOCK &&
        !GetHasSpellEffect(SPELL_CATS_GRACE, OBJECT_SELF) &&
        UAI_UtilitySpellReady(SPELL_CATS_GRACE))
        n += 1; // conservative minimum skill gain from +DEX

    if (nSkill == SKILL_DISABLE_TRAP &&
        !GetHasSpellEffect(SPELL_FOXS_CUNNING, OBJECT_SELF) &&
        UAI_UtilitySpellReady(SPELL_FOXS_CUNNING))
        n += 1; // conservative minimum skill gain from +INT

    return n;
}

int UAI_TryUtilityBuff(int nSkill, int nNeed)
{
    if (nNeed <= 0) return FALSE;
    int nPotential = UAI_UtilityPotentialBuff(nSkill);
    if (nPotential < nNeed) return FALSE;

    if (nSkill == SKILL_OPEN_LOCK &&
        !GetHasSpellEffect(SPELL_CATS_GRACE, OBJECT_SELF) &&
        UAI_UtilitySpellReady(SPELL_CATS_GRACE))
    {
        ActionCastSpellAtObject(SPELL_CATS_GRACE, OBJECT_SELF);
        SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "BUFF_CATS_GRACE");
        return TRUE;
    }

    if (nSkill == SKILL_DISABLE_TRAP &&
        !GetHasSpellEffect(SPELL_FOXS_CUNNING, OBJECT_SELF) &&
        UAI_UtilitySpellReady(SPELL_FOXS_CUNNING))
    {
        ActionCastSpellAtObject(SPELL_FOXS_CUNNING, OBJECT_SELF);
        SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "BUFF_FOXS_CUNNING");
        return TRUE;
    }

    return FALSE;
}

int UAI_TryTrap()
{
    if (GetSkillRank(SKILL_DISABLE_TRAP, OBJECT_SELF) <= 0) return FALSE;

    object oTrap = GetNearestTrapToObject(OBJECT_SELF, TRUE);
    if (!GetIsObjectValid(oTrap) || !GetTrapActive(oTrap)) return FALSE;
    if (GetArea(oTrap) != GetArea(OBJECT_SELF)) return FALSE;
    if (GetDistanceBetween(OBJECT_SELF, oTrap) > 12.0) return FALSE;

    int nSkill = GetSkillRank(SKILL_DISABLE_TRAP, OBJECT_SELF);
    int nDC = GetTrapDisarmDC(oTrap);
    if (nDC <= 0) return FALSE;

    // NWN1 permits take-20 outside combat. Recover is DC+10; disarm is base DC.
    int nSafe = nSkill + 20;
    int nRecoverDC = nDC + 10;

    if (GetTrapRecoverable(oTrap))
    {
        if (nSafe >= nRecoverDC)
        {
            ActionUseSkill(SKILL_DISABLE_TRAP, oTrap, SUBSKILL_RECOVERTRAP);
            SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "RECOVER_TRAP");
            return TRUE;
        }

        int nNeedRecover = nRecoverDC - nSafe;
        if (UAI_TryUtilityBuff(SKILL_DISABLE_TRAP, nNeedRecover)) return TRUE;
    }

    if (GetTrapDisarmable(oTrap))
    {
        // Base NWN rule: non-rogues cannot disarm the highest-DC traps.
        if (nDC > 35 && GetLevelByClass(CLASS_TYPE_ROGUE, OBJECT_SELF) <= 0)
        {
            SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "TRAP_NEEDS_ROGUE");
            return FALSE;
        }

        if (nSafe >= nDC)
        {
            ActionUseSkill(SKILL_DISABLE_TRAP, oTrap);
            SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "DISARM_TRAP");
            return TRUE;
        }

        int nNeedDisarm = nDC - nSafe;
        if (UAI_TryUtilityBuff(SKILL_DISABLE_TRAP, nNeedDisarm)) return TRUE;
    }

    SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "TRAP_UNSAFE");
    return FALSE;
}

object UAI_FindSafeLockedObject()
{
    int nNth;
    for (nNth = 1; nNth <= 12; nNth++)
    {
        object o = GetNearestObject(OBJECT_TYPE_DOOR | OBJECT_TYPE_PLACEABLE, OBJECT_SELF, nNth);
        if (!GetIsObjectValid(o)) break;
        if (GetDistanceBetween(OBJECT_SELF, o) > 12.0) break;
        if (!GetLocked(o) || GetPlotFlag(o)) continue;
        if (!LineOfSightObject(OBJECT_SELF, o)) continue;
        return o;
    }
    return OBJECT_INVALID;
}

int UAI_TryLock()
{
    if (GetSkillRank(SKILL_OPEN_LOCK, OBJECT_SELF) <= 0) return FALSE;

    object oLock = UAI_FindSafeLockedObject();
    if (!GetIsObjectValid(oLock)) return FALSE;

    if (GetLockKeyRequired(oLock))
    {
        string sKey = GetLockKeyTag(oLock);
        if (sKey == "" || !GetIsObjectValid(GetItemPossessedBy(OBJECT_SELF, sKey)))
        {
            SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "LOCK_NEEDS_KEY");
            return FALSE;
        }

        ActionUnlockObject(oLock);
        SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "UNLOCK_WITH_KEY");
        return TRUE;
    }

    int nDC = GetLockUnlockDC(oLock);
    if (nDC <= 0) return FALSE;

    int nSkill = GetSkillRank(SKILL_OPEN_LOCK, OBJECT_SELF);
    int nSafe = nSkill + 20;
    if (nSafe >= nDC)
    {
        ActionUnlockObject(oLock);
        SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "OPEN_LOCK");
        return TRUE;
    }

    int nNeed = nDC - nSafe;
    if (UAI_TryUtilityBuff(SKILL_OPEN_LOCK, nNeed)) return TRUE;

    SetLocalString(OBJECT_SELF, "UAI_LAST_UTILITY", "LOCK_UNSAFE");
    return FALSE;
}

void main()
{
    if (!GetLocalInt(OBJECT_SELF, UAI_MARK)) return;
    if (GetLocalInt(OBJECT_SELF, "UAI_UTILITIES_DISABLED")) return;
    if (GetIsInCombat(OBJECT_SELF) || GetCurrentHitPoints(OBJECT_SELF) <= 0) return;

    // Never steal an explicit player/EPC action. Utility only runs from a truly idle queue.
    if (GetCurrentAction(OBJECT_SELF) != ACTION_INVALID) return;

    object oMaster = GetLocalObject(OBJECT_SELF, UAI_MASTER);
    if (!GetIsObjectValid(oMaster) || !GetIsPC(oMaster) || GetMaster(OBJECT_SELF) != oMaster) return;
    if (GetArea(OBJECT_SELF) != GetArea(oMaster)) return;

    // Traps first: walking a lockpicker through a known trap to reach a lock is unacceptable.
    if (UAI_TryTrap()) return;
    UAI_TryLock();
}
