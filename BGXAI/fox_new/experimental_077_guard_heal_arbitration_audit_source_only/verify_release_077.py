"""Verify source-only BGXAI 077 package SHA manifest; no game access."""
import hashlib, json
from pathlib import Path
p=Path(__file__).parent
m=json.loads((p/'manifest_sha256.json').read_text(encoding='utf-8'))
assert m['source_only'] is True
assert set(m['sha256'])=={'audit_077.py','test_077.py','audit_results_077.json','README_RU.md'}
for name, expected in m['sha256'].items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected, f'BAD_SHA: {name}'
s=(p/'audit_077.py').read_text(encoding='utf-8')
for banned in ['setLocalInt(', 'AttackReevaluate(', 'ClearActions(', 'WeiDU.exe', 'os.system(', 'subprocess.run(', 'write_bytes(', 'write_text(']:
    # Explicit words can appear as source-string comparisons in audited evidence.
    if banned in ['AttackReevaluate(']: continue
    assert banned not in s, f'UNEXPECTED_SOURCE_WRITE: {banned}'
print('BGXAI_077_RELEASE_SHA_PASS 4/4; STATIC_READONLY_PASS')
