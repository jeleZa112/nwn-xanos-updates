const string UAI_SUPERVISOR_EFFECT_TAG = "UAI_SUPERVISOR_080";

int UAI_HasSupervisorEffect(object oPC)
{
    effect e = GetFirstEffect(oPC);
    while (GetIsEffectValid(e))
    {
        if (GetEffectTag(e) == UAI_SUPERVISOR_EFFECT_TAG) return TRUE;
        e = GetNextEffect(oPC);
    }
    return FALSE;
}

void main()
{
    object oPC = OBJECT_SELF;
    if (!GetIsObjectValid(oPC) || !GetIsPC(oPC) || GetCurrentHitPoints(oPC) <= 0) return;
    if (UAI_HasSupervisorEffect(oPC)) return;

    // EffectRunScript is an EE-native persistent interval mechanism. Unlike a
    // naked DelayCommand loop, the effect is part of the saved creature state,
    // making the supervisor robust across save/load without duplicate loops.
    effect eRun = EffectRunScript("uai_boot", "", "uai_boot", 3.0, "UAI080");
    eRun = ExtraordinaryEffect(eRun);
    eRun = TagEffect(eRun, UAI_SUPERVISOR_EFFECT_TAG);
    ApplyEffectToObject(DURATION_TYPE_PERMANENT, eRun, oPC);
}
