const string UAI_MARK = "UAI_V080_ACTIVE";
const string UAI_PREV_AI = "UAI_PREVIOUS_COMBAT_AI";
const string UAI_MASTER = "UAI_MASTER";
const string UAI_ROLE = "UAI_ROLE";
const string UAI_TICK = "UAI_TICK";
const string UAI_SAVED_CHEST = "UAI_SAVED_CHEST";
const string UAI_GEAR_SWAPPED = "UAI_GEAR_SWAPPED";

int UAI_IsNamedXanos(object o)
{
    if (!GetIsObjectValid(o)) return FALSE;
    string s = GetStringLowerCase(GetTag(o) + " " + GetResRef(o));
    if (FindSubString(s, "xanos") >= 0) return TRUE;
    if (GetLocalInt(o, "XAI_V078_ACTIVE")) return TRUE;
    return FALSE;
}

int UAI_IsEligible(object o, object oPC)
{
    if (!GetIsObjectValid(o) || GetObjectType(o) != OBJECT_TYPE_CREATURE) return FALSE;
    if (o == oPC || GetIsPC(o) || GetCurrentHitPoints(o) <= 0) return FALSE;
    if (!GetCommandable(o) || GetIsDMPossessed(o)) return FALSE;
    if (UAI_IsNamedXanos(o)) return FALSE;

    int nAssoc = GetAssociateType(o);
    // Player-character familiar/summon mechanics are separate and must never be touched here.
    if (nAssoc == ASSOCIATE_TYPE_SUMMONED || nAssoc == ASSOCIATE_TYPE_FAMILIAR) return FALSE;

    object oMaster = GetMaster(o);
    if (nAssoc == ASSOCIATE_TYPE_NONE && oMaster != oPC) return FALSE;
    if (GetIsObjectValid(oMaster) && oMaster != oPC) return FALSE;
    if (GetLocalInt(o, "AI_TURNED_OFF")) return FALSE;
    return TRUE;
}

int UAI_AbilityMod(int nScore)
{
    if (nScore >= 10) return (nScore - 10) / 2;
    return -((11 - nScore) / 2);
}

int UAI_HPPercent(object o)
{
    int nMax = GetMaxHitPoints(o);
    if (nMax <= 0) return 100;
    return (GetCurrentHitPoints(o) * 100) / nMax;
}

int UAI_CasterLevel(object o)
{
    int nTotal = 0;
    int i;
    for (i = 1; i <= 3; i++)
    {
        int nClass = GetClassByPosition(i, o);
        if (nClass == CLASS_TYPE_INVALID) continue;

        int bCaster = FALSE;
        int nSpellLevel;
        for (nSpellLevel = 0; nSpellLevel <= 9; nSpellLevel++)
        {
            if (GetKnownSpellCount(o, nClass, nSpellLevel) > 0)
            {
                bCaster = TRUE;
                break;
            }
        }

        // Prepared stock casters can report no "known" spells in some states.
        if (nClass == CLASS_TYPE_SORCERER || nClass == CLASS_TYPE_WIZARD ||
            nClass == CLASS_TYPE_BARD || nClass == CLASS_TYPE_CLERIC ||
            nClass == CLASS_TYPE_DRUID || nClass == CLASS_TYPE_PALADIN ||
            nClass == CLASS_TYPE_RANGER)
            bCaster = TRUE;

        if (bCaster) nTotal += GetLevelByClass(nClass, o);
    }
    return nTotal;
}

int UAI_HealerLevel(object o)
{
    return GetLevelByClass(CLASS_TYPE_CLERIC, o) +
           GetLevelByClass(CLASS_TYPE_DRUID, o) +
           GetLevelByClass(CLASS_TYPE_PALADIN, o) +
           GetLevelByClass(CLASS_TYPE_BARD, o);
}

int UAI_UtilityScore(object o)
{
    return GetSkillRank(SKILL_OPEN_LOCK, o) +
           GetSkillRank(SKILL_DISABLE_TRAP, o) +
           GetSkillRank(SKILL_SEARCH, o) +
           GetSkillRank(SKILL_USE_MAGIC_DEVICE, o);
}

int UAI_HasManeuver(object o)
{
    return GetHasFeat(FEAT_IMPROVED_KNOCKDOWN, o) || GetHasFeat(FEAT_KNOCKDOWN, o) ||
           GetHasFeat(FEAT_IMPROVED_DISARM, o) || GetHasFeat(FEAT_DISARM, o) ||
           GetHasFeat(FEAT_CALLED_SHOT, o) || GetHasFeat(FEAT_RAPID_SHOT, o) ||
           GetHasFeat(FEAT_POWER_ATTACK, o) || GetHasFeat(FEAT_EXPERTISE, o);
}

int UAI_IsRangedWeaponItem(object oItem)
{
    if (!GetIsObjectValid(oItem) || GetObjectType(oItem) != OBJECT_TYPE_ITEM) return FALSE;
    if (GetWeaponRanged(oItem)) return TRUE;
    int nBase = GetBaseItemType(oItem);
    return (nBase == BASE_ITEM_LONGBOW || nBase == BASE_ITEM_SHORTBOW ||
            nBase == BASE_ITEM_LIGHTCROSSBOW || nBase == BASE_ITEM_HEAVYCROSSBOW ||
            nBase == BASE_ITEM_SLING || nBase == BASE_ITEM_DART ||
            nBase == BASE_ITEM_THROWINGAXE || nBase == BASE_ITEM_SHURIKEN);
}

int UAI_BaseMeleeDamage10(int nBase)
{
    switch (nBase)
    {
        case BASE_ITEM_BASTARDSWORD: return 55;
        case BASE_ITEM_DAGGER: return 25;
        case BASE_ITEM_BATTLEAXE: return 45;
        case BASE_ITEM_CLUB: return 35;
        case BASE_ITEM_DIREMACE: return 55;
        case BASE_ITEM_DOUBLEAXE: return 60;
        case BASE_ITEM_DWARVENWARAXE: return 55;
        case BASE_ITEM_GREATAXE: return 65;
        case BASE_ITEM_GREATSWORD: return 70;
        case BASE_ITEM_HALBERD: return 55;
        case BASE_ITEM_HANDAXE: return 35;
        case BASE_ITEM_HEAVYFLAIL: return 55;
        case BASE_ITEM_KAMA: return 30;
        case BASE_ITEM_KATANA: return 55;
        case BASE_ITEM_KUKRI: return 25;
        case BASE_ITEM_LIGHTFLAIL: return 45;
        case BASE_ITEM_LIGHTHAMMER: return 25;
        case BASE_ITEM_LIGHTMACE: return 35;
        case BASE_ITEM_LONGSWORD: return 45;
        case BASE_ITEM_MORNINGSTAR: return 45;
        case BASE_ITEM_QUARTERSTAFF: return 35;
        case BASE_ITEM_RAPIER: return 35;
        case BASE_ITEM_SCIMITAR: return 35;
        case BASE_ITEM_SCYTHE: return 50;
        case BASE_ITEM_SHORTSPEAR: return 35;
        case BASE_ITEM_SHORTSWORD: return 35;
        case BASE_ITEM_SICKLE: return 35;
        case BASE_ITEM_TRIDENT: return 45;
        case BASE_ITEM_TWOBLADEDSWORD: return 60;
        case BASE_ITEM_WARHAMMER: return 45;
        case BASE_ITEM_WHIP: return 10;
    }
    return -10000;
}

int UAI_RangedDamage10(int nBase)
{
    if (nBase == BASE_ITEM_LONGBOW) return 45;
    if (nBase == BASE_ITEM_SHORTBOW) return 35;
    if (nBase == BASE_ITEM_LIGHTCROSSBOW) return 45;
    if (nBase == BASE_ITEM_HEAVYCROSSBOW) return 55;
    if (nBase == BASE_ITEM_SLING) return 25;
    if (nBase == BASE_ITEM_DART) return 25;
    if (nBase == BASE_ITEM_THROWINGAXE) return 35;
    if (nBase == BASE_ITEM_SHURIKEN) return 15;
    return -10000;
}

int UAI_ItemPropertyMaxValue(object oItem, int nType)
{
    int nBest = 0;
    itemproperty ip = GetFirstItemProperty(oItem);
    while (GetIsItemPropertyValid(ip))
    {
        if (GetItemPropertyType(ip) == nType)
        {
            int n = GetItemPropertyCostTableValue(ip);
            if (n > nBest) nBest = n;
        }
        ip = GetNextItemProperty(oItem);
    }
    return nBest;
}

int UAI_ItemHasPropertyType(object oItem, int nType)
{
    itemproperty ip = GetFirstItemProperty(oItem);
    while (GetIsItemPropertyValid(ip))
    {
        if (GetItemPropertyType(ip) == nType) return TRUE;
        ip = GetNextItemProperty(oItem);
    }
    return FALSE;
}

int UAI_IsFinesseBase(int nBase)
{
    return (nBase == BASE_ITEM_DAGGER || nBase == BASE_ITEM_HANDAXE ||
            nBase == BASE_ITEM_KAMA || nBase == BASE_ITEM_KUKRI ||
            nBase == BASE_ITEM_LIGHTHAMMER || nBase == BASE_ITEM_LIGHTMACE ||
            nBase == BASE_ITEM_RAPIER || nBase == BASE_ITEM_SHORTSWORD ||
            nBase == BASE_ITEM_SICKLE);
}

int UAI_IsTwoHandedBase(int nBase)
{
    return (nBase == BASE_ITEM_GREATAXE || nBase == BASE_ITEM_GREATSWORD ||
            nBase == BASE_ITEM_HALBERD || nBase == BASE_ITEM_HEAVYFLAIL ||
            nBase == BASE_ITEM_QUARTERSTAFF || nBase == BASE_ITEM_SCYTHE ||
            nBase == BASE_ITEM_DIREMACE || nBase == BASE_ITEM_DOUBLEAXE ||
            nBase == BASE_ITEM_TWOBLADEDSWORD);
}

int UAI_MeleeScore(object oItem, object oTarget)
{
    if (!GetIsObjectValid(oItem)) return -100000;
    int nBase = GetBaseItemType(oItem);
    int nDamage10 = UAI_BaseMeleeDamage10(nBase);
    if (nDamage10 < 0 || GetWeaponRanged(oItem)) return -100000;

    int nStr = UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_STRENGTH));
    int nDex = UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_DEXTERITY));
    int nAtkAbility = nStr;
    if (GetHasFeat(FEAT_WEAPON_FINESSE, OBJECT_SELF) && UAI_IsFinesseBase(nBase) && nDex > nStr)
        nAtkAbility = nDex;

    int nEnh = UAI_ItemPropertyMaxValue(oItem, ITEM_PROPERTY_ENHANCEMENT_BONUS);
    int nAtk = UAI_ItemPropertyMaxValue(oItem, ITEM_PROPERTY_ATTACK_BONUS);
    int nAB = GetBaseAttackBonus(OBJECT_SELF) + nAtkAbility + nEnh + nAtk;
    int nHit = 65;
    if (GetIsObjectValid(oTarget))
    {
        int nNeed = GetAC(oTarget) - nAB;
        nHit = (21 - nNeed) * 5;
        if (nHit < 5) nHit = 5;
        if (nHit > 95) nHit = 95;
    }

    int nStrDamage10 = nStr * 10;
    if (UAI_IsTwoHandedBase(nBase)) nStrDamage10 = nStr * 15;
    nDamage10 += nStrDamage10 + nEnh * 10;
    if (nDamage10 < 10) nDamage10 = 10;

    int nScore = (nDamage10 * nHit) / 10 + nAtk * 8;
    if (UAI_ItemHasPropertyType(oItem, ITEM_PROPERTY_DAMAGE_BONUS)) nScore += 20;
    if (oItem == GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF)) nScore += 5;
    return nScore;
}

int UAI_RangedScore(object oItem, object oTarget)
{
    if (!GetIsObjectValid(oItem) || !UAI_IsRangedWeaponItem(oItem)) return -100000;
    int nBase = GetBaseItemType(oItem);
    int nDamage10 = UAI_RangedDamage10(nBase);
    if (nDamage10 < 0) return -100000;
    int nDex = UAI_AbilityMod(GetAbilityScore(OBJECT_SELF, ABILITY_DEXTERITY));
    int nEnh = UAI_ItemPropertyMaxValue(oItem, ITEM_PROPERTY_ENHANCEMENT_BONUS);
    int nAtk = UAI_ItemPropertyMaxValue(oItem, ITEM_PROPERTY_ATTACK_BONUS);
    int nAB = GetBaseAttackBonus(OBJECT_SELF) + nDex + nEnh + nAtk;
    int nHit = 65;
    if (GetIsObjectValid(oTarget))
    {
        int nNeed = GetAC(oTarget) - nAB;
        nHit = (21 - nNeed) * 5;
        if (nHit < 5) nHit = 5;
        if (nHit > 95) nHit = 95;
    }
    int nScore = ((nDamage10 + nEnh * 10) * nHit) / 10 + nAtk * 8;
    if (UAI_ItemHasPropertyType(oItem, ITEM_PROPERTY_DAMAGE_BONUS)) nScore += 20;
    if (oItem == GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF)) nScore += 5;
    return nScore;
}

object UAI_BestMelee(object oTarget)
{
    object oBest = OBJECT_INVALID;
    int nBest = -100000;
    object o = GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF);
    if (GetIsObjectValid(o)) { nBest = UAI_MeleeScore(o, oTarget); if (nBest > -100000) oBest = o; }
    o = GetFirstItemInInventory(OBJECT_SELF);
    while (GetIsObjectValid(o))
    {
        int n = UAI_MeleeScore(o, oTarget);
        if (n > nBest) { nBest = n; oBest = o; }
        o = GetNextItemInInventory(OBJECT_SELF);
    }
    return oBest;
}

object UAI_BestRanged(object oTarget)
{
    object oBest = OBJECT_INVALID;
    int nBest = -100000;
    object o = GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF);
    if (GetIsObjectValid(o)) { nBest = UAI_RangedScore(o, oTarget); if (nBest > -100000) oBest = o; }
    o = GetFirstItemInInventory(OBJECT_SELF);
    while (GetIsObjectValid(o))
    {
        int n = UAI_RangedScore(o, oTarget);
        if (n > nBest) { nBest = n; oBest = o; }
        o = GetNextItemInInventory(OBJECT_SELF);
    }
    return oBest;
}

int UAI_AmmoBaseForWeapon(int nWeaponBase)
{
    if (nWeaponBase == BASE_ITEM_LONGBOW || nWeaponBase == BASE_ITEM_SHORTBOW) return BASE_ITEM_ARROW;
    if (nWeaponBase == BASE_ITEM_LIGHTCROSSBOW || nWeaponBase == BASE_ITEM_HEAVYCROSSBOW) return BASE_ITEM_BOLT;
    if (nWeaponBase == BASE_ITEM_SLING) return BASE_ITEM_BULLET;
    return BASE_ITEM_INVALID;
}

int UAI_AmmoSlot(int nAmmoBase)
{
    if (nAmmoBase == BASE_ITEM_ARROW) return INVENTORY_SLOT_ARROWS;
    if (nAmmoBase == BASE_ITEM_BOLT) return INVENTORY_SLOT_BOLTS;
    if (nAmmoBase == BASE_ITEM_BULLET) return INVENTORY_SLOT_BULLETS;
    return -1;
}

int UAI_TargetDefensePenalty(object oTarget, int nDamageType)
{
    if (!GetIsObjectValid(oTarget)) return 0;
    int nPenalty = 0;
    int i;
    for (i = INVENTORY_SLOT_HEAD; i <= INVENTORY_SLOT_BOLTS; i++)
    {
        object oItem = GetItemInSlot(i, oTarget);
        if (!GetIsObjectValid(oItem)) continue;
        itemproperty ip = GetFirstItemProperty(oItem);
        while (GetIsItemPropertyValid(ip))
        {
            int nType = GetItemPropertyType(ip);
            if (GetItemPropertySubType(ip) == nDamageType)
            {
                if (nType == ITEM_PROPERTY_IMMUNITY_DAMAGE_TYPE) nPenalty += GetItemPropertyCostTableValue(ip) * 18;
                else if (nType == ITEM_PROPERTY_DAMAGE_RESISTANCE) nPenalty += GetItemPropertyCostTableValue(ip) * 12;
                else if (nType == ITEM_PROPERTY_DAMAGE_VULNERABILITY) nPenalty -= GetItemPropertyCostTableValue(ip) * 10;
            }
            ip = GetNextItemProperty(oItem);
        }
    }
    object oSkin = GetItemInSlot(INVENTORY_SLOT_CARMOUR, oTarget);
    if (GetIsObjectValid(oSkin))
    {
        itemproperty ip2 = GetFirstItemProperty(oSkin);
        while (GetIsItemPropertyValid(ip2))
        {
            int nType2 = GetItemPropertyType(ip2);
            if (GetItemPropertySubType(ip2) == nDamageType)
            {
                if (nType2 == ITEM_PROPERTY_IMMUNITY_DAMAGE_TYPE) nPenalty += GetItemPropertyCostTableValue(ip2) * 18;
                else if (nType2 == ITEM_PROPERTY_DAMAGE_RESISTANCE) nPenalty += GetItemPropertyCostTableValue(ip2) * 12;
                else if (nType2 == ITEM_PROPERTY_DAMAGE_VULNERABILITY) nPenalty -= GetItemPropertyCostTableValue(ip2) * 10;
            }
            ip2 = GetNextItemProperty(oSkin);
        }
    }
    return nPenalty;
}

int UAI_IsWeakTarget(object oTarget)
{
    if (!GetIsObjectValid(oTarget) || UAI_IsCasterTarget(oTarget)) return FALSE;

    float fTargetCR = GetChallengeRating(oTarget);
    float fSelfCR = GetChallengeRating(OBJECT_SELF);
    if (fTargetCR > 0.0 && fSelfCR > 0.0 && fTargetCR <= fSelfCR * 0.75) return TRUE;
    if (GetHitDice(oTarget) <= GetHitDice(OBJECT_SELF) - 1) return TRUE;
    if (GetMaxHitPoints(oTarget) * 2 <= GetMaxHitPoints(OBJECT_SELF)) return TRUE;
    return FALSE;
}

int UAI_AmmoScore(object oAmmo, object oTarget)
{
    if (!GetIsObjectValid(oAmmo)) return -100000;
    int nBase = GetBaseItemType(oAmmo);
    if (nBase != BASE_ITEM_ARROW && nBase != BASE_ITEM_BOLT && nBase != BASE_ITEM_BULLET) return -100000;

    int nScore = 10;
    nScore += UAI_ItemPropertyMaxValue(oAmmo, ITEM_PROPERTY_ENHANCEMENT_BONUS) * 36;
    nScore += UAI_ItemPropertyMaxValue(oAmmo, ITEM_PROPERTY_ATTACK_BONUS) * 30;

    int bSpecialDamage = FALSE;
    itemproperty ip = GetFirstItemProperty(oAmmo);
    while (GetIsItemPropertyValid(ip))
    {
        if (GetItemPropertyType(ip) == ITEM_PROPERTY_DAMAGE_BONUS)
        {
            bSpecialDamage = TRUE;
            nScore += GetItemPropertyCostTableValue(ip) * 18;
            nScore -= UAI_TargetDefensePenalty(oTarget, GetItemPropertySubType(ip));
        }
        ip = GetNextItemProperty(oAmmo);
    }

    // Proven Xanos policy generalized: do not burn elemental/special ammo on obvious trash.
    if (bSpecialDamage && UAI_IsWeakTarget(oTarget)) nScore -= 500;

    // Stack size is only a tiny tie-breaker. Quality must dominate quantity.
    int nStack = GetNumStackedItems(oAmmo);
    if (nStack > 100) nStack = 100;
    nScore += nStack / 25;

    int nSlot = UAI_AmmoSlot(nBase);
    if (nSlot >= 0 && oAmmo == GetItemInSlot(nSlot, OBJECT_SELF)) nScore += 2;
    return nScore;
}

object UAI_BestAmmo(int nAmmoBase, object oTarget)
{
    object oBest = OBJECT_INVALID;
    int nBest = -100000;
    object o = GetFirstItemInInventory(OBJECT_SELF);
    while (GetIsObjectValid(o))
    {
        if (GetBaseItemType(o) == nAmmoBase)
        {
            int n = UAI_AmmoScore(o, oTarget);
            if (n > nBest) { nBest = n; oBest = o; }
        }
        o = GetNextItemInInventory(OBJECT_SELF);
    }
    int nSlot = UAI_AmmoSlot(nAmmoBase);
    if (nSlot >= 0)
    {
        o = GetItemInSlot(nSlot, OBJECT_SELF);
        if (GetIsObjectValid(o) && GetBaseItemType(o) == nAmmoBase)
        {
            int n2 = UAI_AmmoScore(o, oTarget);
            if (n2 >= nBest) oBest = o;
        }
    }
    return oBest;
}

int UAI_ThreatDamageTypeFromItem(object oItem)
{
    if (!GetIsObjectValid(oItem)) return -1;
    int nBestType = -1;
    int nBest = 0;
    itemproperty ip = GetFirstItemProperty(oItem);
    while (GetIsItemPropertyValid(ip))
    {
        if (GetItemPropertyType(ip) == ITEM_PROPERTY_DAMAGE_BONUS)
        {
            int n = GetItemPropertyCostTableValue(ip);
            if (n > nBest) { nBest = n; nBestType = GetItemPropertySubType(ip); }
        }
        ip = GetNextItemProperty(oItem);
    }
    return nBestType;
}

int UAI_ThreatDamageType(object oTarget)
{
    if (!GetIsObjectValid(oTarget)) return -1;
    int n = UAI_ThreatDamageTypeFromItem(GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, oTarget));
    if (n >= 0) return n;
    n = UAI_ThreatDamageTypeFromItem(GetItemInSlot(INVENTORY_SLOT_ARROWS, oTarget)); if (n >= 0) return n;
    n = UAI_ThreatDamageTypeFromItem(GetItemInSlot(INVENTORY_SLOT_BOLTS, oTarget)); if (n >= 0) return n;
    n = UAI_ThreatDamageTypeFromItem(GetItemInSlot(INVENTORY_SLOT_BULLETS, oTarget)); if (n >= 0) return n;
    return UAI_ThreatDamageTypeFromItem(GetItemInSlot(INVENTORY_SLOT_CARMOUR, oTarget));
}

int UAI_ArmorProtectionScore(object oItem, int nDamageType)
{
    if (!GetIsObjectValid(oItem) || GetBaseItemType(oItem) != BASE_ITEM_ARMOR) return -100000;

    int nScore = GetItemACValue(oItem) * 18;
    itemproperty ip = GetFirstItemProperty(oItem);
    while (GetIsItemPropertyValid(ip))
    {
        int nType = GetItemPropertyType(ip);
        if (GetItemPropertySubType(ip) == nDamageType)
        {
            int nCost = GetItemPropertyCostTableValue(ip);
            if (nType == ITEM_PROPERTY_IMMUNITY_DAMAGE_TYPE) nScore += 500 + nCost * 20;
            else if (nType == ITEM_PROPERTY_DAMAGE_RESISTANCE) nScore += 300 + nCost * 15;
            else if (nType == ITEM_PROPERTY_DAMAGE_VULNERABILITY) nScore -= 500 + nCost * 15;
        }

        if (nType == ITEM_PROPERTY_AC_BONUS) nScore += GetItemPropertyCostTableValue(ip) * 8;
        else if (nType == ITEM_PROPERTY_SAVING_THROW_BONUS) nScore += GetItemPropertyCostTableValue(ip) * 4;
        else if (nType == ITEM_PROPERTY_SAVING_THROW_BONUS_SPECIFIC) nScore += GetItemPropertyCostTableValue(ip) * 3;
        ip = GetNextItemProperty(oItem);
    }

    if (oItem == GetItemInSlot(INVENTORY_SLOT_CHEST, OBJECT_SELF)) nScore += 20;
    return nScore;
}

int UAI_AdaptArmor(object oTarget)
{
    int nDamageType = UAI_ThreatDamageType(oTarget);
    if (nDamageType < 0) return FALSE;

    object oCurrent = GetItemInSlot(INVENTORY_SLOT_CHEST, OBJECT_SELF);
    object oBest = oCurrent;
    int nBest = UAI_ArmorProtectionScore(oCurrent, nDamageType);
    int nCurrentBaseAC = GetIsObjectValid(oCurrent) ? GetItemACValue(oCurrent) : 0;
    int bCaster = UAI_CasterLevel(OBJECT_SELF) > 0;

    object o = GetFirstItemInInventory(OBJECT_SELF);
    while (GetIsObjectValid(o))
    {
        if (GetBaseItemType(o) == BASE_ITEM_ARMOR && GetIdentified(o))
        {
            int n = UAI_ArmorProtectionScore(o, nDamageType);

            // Conservative ASF / casting-safety proxy:
            // a spell-capable companion will not jump from light clothing into substantially
            // heavier armor just for a resistance unless already in an emergency.
            if (bCaster && GetItemACValue(o) > nCurrentBaseAC + 1 && UAI_HPPercent(OBJECT_SELF) > 25)
                n -= 900;

            if (n > nBest + 50)
            {
                nBest = n;
                oBest = o;
            }
        }
        o = GetNextItemInInventory(OBJECT_SELF);
    }

    if (GetIsObjectValid(oBest) && oBest != oCurrent)
    {
        if (!GetLocalInt(OBJECT_SELF, "UAI_GEAR_PENDING") && !GetLocalInt(OBJECT_SELF, UAI_GEAR_SWAPPED))
        {
            SetLocalObject(OBJECT_SELF, UAI_SAVED_CHEST, oCurrent);
            SetLocalObject(OBJECT_SELF, "UAI_TEMP_CHEST", oBest);
        }

        SetLocalInt(OBJECT_SELF, "UAI_GEAR_PENDING", TRUE);
        ActionEquipItem(oBest, INVENTORY_SLOT_CHEST);
        ActionDoCommand(SetLocalInt(OBJECT_SELF, UAI_GEAR_SWAPPED, TRUE));
        ActionDoCommand(DeleteLocalInt(OBJECT_SELF, "UAI_GEAR_PENDING"));
        SetLocalString(OBJECT_SELF, "UAI_LAST_GEAR_REASON", "ELEMENT_RESIST");
        return TRUE;
    }
    return FALSE;
}

void UAI_RestoreArmor(object o)
{
    if (!GetLocalInt(o, UAI_GEAR_SWAPPED)) return;

    object oSaved = GetLocalObject(o, UAI_SAVED_CHEST);
    object oTemp = GetLocalObject(o, "UAI_TEMP_CHEST");
    object oCurrent = GetItemInSlot(INVENTORY_SLOT_CHEST, o);

    // If the player changed armor manually after UAI's swap, manual choice wins.
    if (GetIsObjectValid(oTemp) && oCurrent != oTemp)
    {
        DeleteLocalInt(o, UAI_GEAR_SWAPPED);
        DeleteLocalInt(o, "UAI_GEAR_PENDING");
        DeleteLocalObject(o, UAI_SAVED_CHEST);
        DeleteLocalObject(o, "UAI_TEMP_CHEST");
        return;
    }

    if (GetIsObjectValid(oSaved) && oCurrent != oSaved)
    {
        AssignCommand(o, ActionEquipItem(oSaved, INVENTORY_SLOT_CHEST));
        AssignCommand(o, ActionDoCommand(DeleteLocalInt(o, UAI_GEAR_SWAPPED)));
        AssignCommand(o, ActionDoCommand(DeleteLocalInt(o, "UAI_GEAR_PENDING")));
        AssignCommand(o, ActionDoCommand(DeleteLocalObject(o, UAI_SAVED_CHEST)));
        AssignCommand(o, ActionDoCommand(DeleteLocalObject(o, "UAI_TEMP_CHEST")));
    }
    else
    {
        DeleteLocalInt(o, UAI_GEAR_SWAPPED);
        DeleteLocalInt(o, "UAI_GEAR_PENDING");
        DeleteLocalObject(o, UAI_SAVED_CHEST);
        DeleteLocalObject(o, "UAI_TEMP_CHEST");
    }
}

int UAI_IsCasterTarget(object o)
{
    if (!GetIsObjectValid(o)) return FALSE;
    if (GetCurrentAction(o) == ACTION_CASTSPELL || GetCurrentAction(o) == ACTION_ITEMCASTSPELL) return TRUE;
    return UAI_CasterLevel(o) > 0;
}



int UAI_TargetScore(object o, object oMaster)
{
    if (!GetIsObjectValid(o) || GetObjectType(o) != OBJECT_TYPE_CREATURE || GetCurrentHitPoints(o) <= 0) return -100000;
    int bEnemy = GetIsEnemy(o, OBJECT_SELF);
    int bUs = GetAttackTarget(o) == OBJECT_SELF;
    int bMaster = GetIsObjectValid(oMaster) && GetAttackTarget(o) == oMaster;
    int bWe = GetAttackTarget(OBJECT_SELF) == o;
    int bMasterAtk = GetIsObjectValid(oMaster) && GetAttackTarget(oMaster) == o;
    if (!bEnemy && !bUs && !bMaster && !bWe && !bMasterAtk) return -100000;
    float f = GetDistanceBetween(OBJECT_SELF, o);
    if (!bUs && !bMaster && !bWe && !bMasterAtk && f > 14.0) return -100000;
    int n = 0;
    if (UAI_IsCasterTarget(o)) n += 600;
    if (bMaster) n += 700;
    if (bMasterAtk) n += 1000;
    if (bUs) n += 800;
    if (f <= 5.0) n += 500;
    n += GetHitDice(o) * 8;
    n += 100 - UAI_HPPercent(o);
    return n;
}

object UAI_SelectTarget()
{
    object oMaster = GetLocalObject(OBJECT_SELF, UAI_MASTER);
    if (!GetIsObjectValid(oMaster)) oMaster = GetMaster(OBJECT_SELF);
    object oBest = OBJECT_INVALID;
    int nBest = -100000;
    object oMasterTarget = GetIsObjectValid(oMaster) ? GetAttackTarget(oMaster) : OBJECT_INVALID;
    if (GetIsObjectValid(oMasterTarget))
    {
        int nM = UAI_TargetScore(oMasterTarget, oMaster);
        if (nM > nBest) { nBest = nM; oBest = oMasterTarget; }
    }
    object o = GetFirstObjectInShape(SHAPE_SPHERE, 22.0, GetLocation(OBJECT_SELF), TRUE, OBJECT_TYPE_CREATURE);
    while (GetIsObjectValid(o))
    {
        if (o != OBJECT_SELF && o != oMaster)
        {
            int n = UAI_TargetScore(o, oMaster);
            if (n > nBest) { nBest = n; oBest = o; }
        }
        o = GetNextObjectInShape(SHAPE_SPHERE, 22.0, GetLocation(OBJECT_SELF), TRUE, OBJECT_TYPE_CREATURE);
    }
    if (!GetIsObjectValid(oBest))
    {
        object oAtk = GetAttackTarget(OBJECT_SELF);
        if (GetIsObjectValid(oAtk) && GetDistanceBetween(OBJECT_SELF, oAtk) <= 22.0) oBest = oAtk;
    }
    if (!GetIsObjectValid(oBest))
    {
        object oLast = GetLastAttacker(OBJECT_SELF);
        if (GetIsObjectValid(oLast) && GetDistanceBetween(OBJECT_SELF, oLast) <= 22.0) oBest = oLast;
    }
    return oBest;
}

int UAI_HasRangedInventory(object o)
{
    object it = GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, o);
    if (GetIsObjectValid(it) && UAI_IsRangedWeaponItem(it)) return TRUE;
    it = GetFirstItemInInventory(o);
    while (GetIsObjectValid(it))
    {
        if (UAI_IsRangedWeaponItem(it)) return TRUE;
        it = GetNextItemInInventory(o);
    }
    return FALSE;
}

string UAI_DetectRole(object o)
{
    int nHD = GetHitDice(o);
    int nCaster = UAI_CasterLevel(o);
    int nUtility = UAI_UtilityScore(o);
    int nStr = GetAbilityScore(o, ABILITY_STRENGTH);
    int nDex = GetAbilityScore(o, ABILITY_DEXTERITY);

    int nMelee = 0;
    int nRanged = 0;
    object it = GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, o);
    if (GetIsObjectValid(it))
    {
        if (UAI_IsRangedWeaponItem(it)) nRanged += 2;
        else if (UAI_BaseMeleeDamage10(GetBaseItemType(it)) > 0) nMelee += 2;
    }
    it = GetFirstItemInInventory(o);
    while (GetIsObjectValid(it))
    {
        if (UAI_IsRangedWeaponItem(it)) nRanged++;
        else if (UAI_BaseMeleeDamage10(GetBaseItemType(it)) > 0) nMelee++;
        it = GetNextItemInInventory(o);
    }

    if (UAI_HealerLevel(o) > 0 && nCaster * 2 >= nHD) return "HEALER";
    if (nCaster * 2 >= nHD) return "CASTER";
    if (nUtility >= 12 && nRanged > 0) return "UTILITY_RANGED";
    if (nUtility >= 12) return "UTILITY";
    if (nRanged > 0 && (nDex >= nStr + 2 || nRanged > nMelee)) return "RANGED";
    if (nCaster > 0) return "HYBRID";
    return "MELEE";
}

void UAI_Profile(object o)
{
    string sRole = UAI_DetectRole(o);
    SetLocalString(o, UAI_ROLE, sRole);
    SetLocalInt(o, "UAI_CAP_CASTER", UAI_CasterLevel(o) > 0);
    SetLocalInt(o, "UAI_CAP_HEALER", UAI_HealerLevel(o) > 0);
    SetLocalInt(o, "UAI_CAP_UTILITY", UAI_UtilityScore(o) >= 8);
    SetLocalInt(o, "UAI_CAP_MANEUVERS", UAI_HasManeuver(o));
    SetLocalInt(o, "UAI_CAP_RANGED", UAI_HasRangedInventory(o));
    SetLocalString(o, "UAI_EQUIPPED_CHEST", GetName(GetItemInSlot(INVENTORY_SLOT_CHEST, o)));
}

void UAI_DetachAndFallback()
{
    string sPrev = GetLocalString(OBJECT_SELF, UAI_PREV_AI);
    if (sPrev != "" && sPrev != "uai_combat")
        SetLocalString(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT", sPrev);
    else
        DeleteLocalString(OBJECT_SELF, "X2_SPECIAL_COMBAT_AI_SCRIPT");

    DeleteLocalInt(OBJECT_SELF, UAI_MARK);
    DeleteLocalObject(OBJECT_SELF, UAI_MASTER);
    DeleteLocalString(OBJECT_SELF, UAI_ROLE);

    if (sPrev != "" && sPrev != "uai_combat") ExecuteScript(sPrev, OBJECT_SELF);
}

void UAI_Fallback()
{
    string sPrev = GetLocalString(OBJECT_SELF, UAI_PREV_AI);
    if (sPrev != "" && sPrev != "uai_combat") ExecuteScript(sPrev, OBJECT_SELF);
}

int UAI_TryManeuver(object oTarget, int bRanged)
{
    if (!GetIsObjectValid(oTarget)) return FALSE;
    int nTick = GetLocalInt(OBJECT_SELF, UAI_TICK);
    int nLast = GetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK");
    if (nTick - nLast < 4) return FALSE;
    float fDist = GetDistanceBetween(OBJECT_SELF, oTarget);
    if (!bRanged && fDist <= 3.5)
    {
        if (!GetIsImmune(oTarget, IMMUNITY_TYPE_KNOCKDOWN, OBJECT_SELF))
        {
            if (GetHasFeat(FEAT_IMPROVED_KNOCKDOWN, OBJECT_SELF))
            { ActionUseFeat(FEAT_IMPROVED_KNOCKDOWN, oTarget); SetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK", nTick); return TRUE; }
            if (GetHasFeat(FEAT_KNOCKDOWN, OBJECT_SELF))
            { ActionUseFeat(FEAT_KNOCKDOWN, oTarget); SetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK", nTick); return TRUE; }
        }
        object oTheirWeapon = GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, oTarget);
        if (GetIsObjectValid(oTheirWeapon) && !GetWeaponRanged(oTheirWeapon))
        {
            if (GetHasFeat(FEAT_IMPROVED_DISARM, OBJECT_SELF))
            { ActionUseFeat(FEAT_IMPROVED_DISARM, oTarget); SetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK", nTick); return TRUE; }
            if (GetHasFeat(FEAT_DISARM, OBJECT_SELF) && GetHitDice(oTarget) <= GetHitDice(OBJECT_SELF) + 1)
            { ActionUseFeat(FEAT_DISARM, oTarget); SetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK", nTick); return TRUE; }
        }
    }
    else if (bRanged && fDist >= 5.0 && GetHasFeat(FEAT_CALLED_SHOT, OBJECT_SELF))
    {
        int nSub = UAI_IsRangedWeaponItem(GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, oTarget)) ? SUBFEAT_CALLED_SHOT_ARMS : SUBFEAT_CALLED_SHOT_LEG;
        ActionUseFeat(FEAT_CALLED_SHOT, oTarget, nSub);
        SetLocalInt(OBJECT_SELF, "UAI_FEAT_TICK", nTick);
        return TRUE;
    }
    return FALSE;
}

int UAI_EquipMelee(object oTarget)
{
    object oBest = UAI_BestMelee(oTarget);
    if (!GetIsObjectValid(oBest)) return FALSE;
    if (GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF) != oBest)
        ActionEquipItem(oBest, INVENTORY_SLOT_RIGHTHAND);
    return TRUE;
}

int UAI_EquipRanged(object oTarget)
{
    object oBest = UAI_BestRanged(oTarget);
    if (!GetIsObjectValid(oBest)) return FALSE;
    if (GetItemInSlot(INVENTORY_SLOT_RIGHTHAND, OBJECT_SELF) != oBest)
        ActionEquipItem(oBest, INVENTORY_SLOT_RIGHTHAND);
    int nAmmoBase = UAI_AmmoBaseForWeapon(GetBaseItemType(oBest));
    if (nAmmoBase != BASE_ITEM_INVALID)
    {
        object oAmmo = UAI_BestAmmo(nAmmoBase, oTarget);
        int nSlot = UAI_AmmoSlot(nAmmoBase);
        if (GetIsObjectValid(oAmmo) && nSlot >= 0 && GetItemInSlot(nSlot, OBJECT_SELF) != oAmmo)
            ActionEquipItem(oAmmo, nSlot);
    }
    return TRUE;
}

void UAI_Attach(object o, object oPC)
{
    if (!UAI_IsEligible(o, oPC)) return;
    SetLocalObject(o, UAI_MASTER, oPC);

    string sCurrent = GetLocalString(o, "X2_SPECIAL_COMBAT_AI_SCRIPT");

    if (!GetLocalInt(o, UAI_MARK))
    {
        if (sCurrent != "" && sCurrent != "uai_combat") SetLocalString(o, UAI_PREV_AI, sCurrent);
        SetLocalInt(o, UAI_MARK, TRUE);
        SetLocalString(o, "X2_SPECIAL_COMBAT_AI_SCRIPT", "uai_combat");
        DeleteLocalInt(o, "UAI_EXTERNAL_OVERRIDE");
        UAI_Profile(o);
        SendMessageToPC(oPC, "[UAI] " + GetName(o) + " attached. Role=" + GetLocalString(o, UAI_ROLE));
        return;
    }

    if (sCurrent == "uai_combat")
    {
        DeleteLocalInt(o, "UAI_EXTERNAL_OVERRIDE");
        return;
    }

    // Another module/system deliberately replaced the special AI after UAI attached.
    // Do not fight it every three seconds; suspend UAI until that external script is cleared.
    if (sCurrent != "")
    {
        SetLocalInt(o, "UAI_EXTERNAL_OVERRIDE", TRUE);
        return;
    }

    // External override ended/cleared: safely resume our wrapper.
    DeleteLocalInt(o, "UAI_EXTERNAL_OVERRIDE");
    SetLocalString(o, "X2_SPECIAL_COMBAT_AI_SCRIPT", "uai_combat");
}
