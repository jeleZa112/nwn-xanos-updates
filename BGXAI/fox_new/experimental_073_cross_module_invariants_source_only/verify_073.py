from pathlib import Path
import hashlib, json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest_sha256.json').read_text(encoding='utf-8'))
for name,h in manifest.items():
    p=root/name
    assert p.is_file(),name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h, name
    print('SHA_PASS',name)
for n in ['BGXAI073_CROSS_MODULE_AUDIT.lua','BGXAI072_EPS_FIRST_ARBITER.lua','BGXAI071_KIT_HINTS_READONLY.lua','BGXAI070_EEEX_FACTS_READONLY.lua','BGXAI069_ROLE_OBSERVER.lua']:
    s=(root/n).read_text()
    for forbidden in ['setLocalInt(', 'ClearActions(', 'AttackReevaluate(', 'ProtectObject(', 'Spell(', 'EEex_Sprite_AddBlock', 'EEex_GameObject_Set']:
        assert forbidden not in s,(n,forbidden)
print('BGXAI073_PASSIVE_ONLY_VERIFIED')
