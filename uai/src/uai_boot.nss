#include "uai_core"

void main()
{
    object oPC = OBJECT_SELF;
    if (!GetIsObjectValid(oPC) || !GetIsPC(oPC)) return;

    int nSupervisorTick = GetLocalInt(oPC, "UAI_SUPERVISOR_TICK") + 1;
    SetLocalInt(oPC, "UAI_SUPERVISOR_TICK", nSupervisorTick);

    object o = GetFirstFactionMember(oPC, FALSE);
    while (GetIsObjectValid(o))
    {
        if (UAI_IsEligible(o, oPC))
        {
            UAI_Attach(o, oPC);

            if (!GetIsInCombat(o))
            {
                UAI_RestoreArmor(o);

                // Refresh the capability snapshot out of combat at a low frequency.
                if ((nSupervisorTick % 4) == 0) UAI_Profile(o);

                // Utility actions are a separate safe layer and only act from an idle queue.
                if (GetCurrentAction(o) == ACTION_INVALID &&
                    GetArea(o) == GetArea(oPC) &&
                    !GetLocalInt(o, "UAI_EXTERNAL_OVERRIDE"))
                    ExecuteScript("uai_utility", o);
            }
        }
        o = GetNextFactionMember(oPC, FALSE);
    }

    DelayCommand(3.0, ExecuteScript("uai_boot", oPC));
}
