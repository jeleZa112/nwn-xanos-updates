"""Offline source safety and exact checksum gate for BGXAI070. No game access."""
from __future__ import annotations
import hashlib
import json
import pathlib
import re

HERE=pathlib.Path(__file__).resolve().parent
EXPECTED_NAME='BGXAI_070_MANIFEST_SHA256.json'

def verify():
    manifest=json.loads((HERE/EXPECTED_NAME).read_text(encoding='utf-8'))
    assert manifest['status']=='SOURCE_ONLY_NOT_INSTALLED'
    for basename, expected in manifest['files'].items():
        assert basename==pathlib.Path(basename).name and '..' not in basename
        p=HERE/basename
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest==expected, (basename,digest,expected)
    old=(HERE/'BGXAI069_ROLE_OBSERVER.lua').read_text(encoding='utf-8')
    new=(HERE/'BGXAI070_EEEX_FACTS_READONLY.lua').read_text(encoding='utf-8')
    # A static guard, NOT a proof of full Lua runtime semantics / EEex compatibility.
    for name,source in [('069',old),('070',new)]:
        code='\n'.join(line.split('--')[0] for line in source.splitlines())
        prohibited=(
            r'\b(?:setLocalInt|ClearActions|Attack|AttackReevaluate|ProtectObject|Spell|ForceSpell)\s*\(',
            r'\b(?:EEex_Sprite_Add\w*Listener|EEex_GameObject_Get|EEex_Read(?:8|16|32|64)|EEex_Write\w*)\s*\(',
            r'\b(?:io\.open|os\.execute|loadfile|dofile|require|loadstring)\s*\(',
        )
        for pattern in prohibited:
            assert re.search(pattern,code) is None, (name,pattern)
    assert 'getLocalInt(\'BGX38_GUARD\')' in new
    assert 'm_nKit' in new and 'm_bPolymorphed' in new
    assert 'engine_orders_sent=0' in new and "kit_verified=false" in new
    print('BGXAI070_MANIFEST_AND_SOURCE_ONLY_SAFETY_PASS',len(manifest['files']),'files')

if __name__=='__main__':
    verify()
