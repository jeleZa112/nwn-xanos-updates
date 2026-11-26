from pathlib import Path
p=Path("BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/M_BGXR27_R37_SOURCE_ONLY.lua")
q=Path("BGXAI/BUILD/R37_INVENTORY16_SINGLE_CALLBACK_SOURCEONLY_20261126/M_BGXR27_R37_INV3_SOURCE_ONLY.lua")
orig=p.read_text(encoding="utf-8")
comp=q.read_text(encoding="utf-8")
def span(source,start,end):
 a=source.index(start)
 b=source.index(end,a+len(start))
 return source[a:b].rstrip()
# Exact legacy R33/R37 serializer bodies preserved, including original order.
assert span(orig, "function R27.toConsoleJson(sample)", "-- R37 emits a second bounded JSON") == span(comp, "function R27.toConsoleJson(sample)", "-- R37 emits a second bounded JSON")
assert span(orig, "function R27.toR37AdviceJson(sample)", "-- Makes a passive console sink") == span(comp, "function R27.toR37AdviceJson(sample)", "-- Uses original R37 EEex raw readers")
assert comp.count("function R27.makeListener(deps)")==1
assert comp.count("EEex_Action_AddSpriteStartedActionListener,pilot.listener")==1
assert comp.count("pcall(R27.captureInventoryV3,sprite,action,result)")==1
assert comp.count("INV3.capture(sprite,sample,contextReader)")==1
assert "for slot=18,33 do" in comp and "for s=18,33 do" in comp
assert "for slot=15,34 do" not in comp
assert "queuedActionsRaw=q.queue_count_raw" in comp
assert "currentScriptNumberRaw=q.current_script_number_raw" in comp
assert "safeActionBoundaryVerified\":false" in comp
assert "inventoryMoveAuthorized\":false" in comp
assert "XEquipItem(" not in comp and "FillSlot(" not in comp
print("PASS R37+INV3 source-only composition integrity and one-hook constraint")
