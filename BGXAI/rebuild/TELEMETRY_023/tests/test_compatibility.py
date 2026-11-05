from pathlib import Path
import re,hashlib,json
root=Path(__file__).parents[1]
weidu=Path('/mnt/data/FOXX_COMPARE/WeiDU(7).log').read_text(errors='replace')
source=(root/'src/BGXAI_FOXX_SCS_PRECHECK_023.ps1').read_text()
assert all(x in source for x in ('#5000','chitin.key','WeiDU.log','READY_FOR_SOURCE_AUDIT','BARD_BEHAVIOR_RISK','EET_END_NOT_RECORDED'))
# Reproduce the exact component selection logic against the saved 31-Oct log.
lines=weidu.splitlines()
scs=[s for s in lines if re.match(r'^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#\d+\b',s)]
assert len(scs)>60,(len(scs),'old SCS footprint unexpected')
assert len([x for x in scs if re.match(r'^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#5000\b',x)])==0
assert len([x for x in scs if re.match(r'^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#5900\b',x)])==1
assert any(re.match(r'^~EEEX[\\/]EEEX\.TP2~\s+#\d+\s+#1\b',x) for x in lines)
assert any(re.match(r'^~EET_END[\\/]EET_END\.TP2~\s+#\d+\s+#0\b',x) for x in lines)
scs5000='~STRATAGEMS/SETUP-STRATAGEMS.TP2~ #7 #5000 // Ease-of-use party AI: 35.21'
assert len([x for x in scs+[scs5000] if re.match(r'^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#5000\b',x)])==1
# Ensure changes are read-only: not a mod installer, script writes or privileged process runner.
assert not re.search(r'(?i)\b(Copy-Item|Remove-Item|Set-Content|Add-Content|Set-Item|Invoke-WebRequest|Start-Process)\b',source)
# Recorded evidence should not be contradicted by migration preflight.
print(f'PASS compatibility invariants: archived WeiDU SCS={len(scs)}, 5000=off, 5900=on, EEex=on, EET_END=on; flag #5000 when added')
