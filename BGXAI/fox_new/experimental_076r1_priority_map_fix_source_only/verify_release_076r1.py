"""Offline source-only release verifier. No engine/game access."""
import hashlib, json, pathlib, sys
base=pathlib.Path(__file__).resolve().parent
manifest=json.loads((base/'manifest_sha256.json').read_text(encoding='utf-8'))
for name, expected in manifest['files'].items():
    actual=hashlib.sha256((base/name).read_bytes()).hexdigest()
    if actual!=expected: raise SystemExit(f'ERROR_MANIFEST_SHA256_MISMATCH: {name}')
assert manifest['files']['verify_066s_live_075.py']=='f1f46df61a168e489746c9bab369c46bb72b9bad40c635b5d6d355c66e22677a'
code=(base/'audit_priority_076r1.py').read_text()
for forbidden in ('write_bytes(','.write_text(','.write(', 'subprocess.', 'requests.', 'urllib.request', 'setLocalInt', 'ClearActions', 'AttackReevaluate', 'ProtectObject('):
    if forbidden in code: raise SystemExit('ERROR_FORBIDDEN_WRITE_OR_ENGINE_ACTION: '+forbidden)
print('BGXAI_076R1_SOURCE_ONLY_SHA_AND_NO_GAME_WRITE_PASS', len(manifest['files']))
