#include "uai_core"

void main()
{
    object oPC = OBJECT_SELF;
    if (!GetIsObjectValid(oPC) || !GetIsPC(oPC)) return;

    object o = GetFirstFactionMember(oPC, FALSE);
    while (GetIsObjectValid(o))
    {
        if (UAI_IsEligible(o, oPC))
        {
            UAI_Attach(o, oPC);
            if (!GetIsInCombat(o)) UAI_RestoreArmor(o);
        }
        o = GetNextFactionMember(oPC, FALSE);
    }

    DelayCommand(3.0, ExecuteScript("uai_boot", oPC));
}
