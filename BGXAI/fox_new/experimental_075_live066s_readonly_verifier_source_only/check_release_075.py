#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest_sha256.json').read_text(encoding='utf-8'))
for name,digest in manifest['files'].items():
    if name.startswith('.') or '/' in name or '\\' in name: raise SystemExit('UNSAFE_PATH')
    actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if actual!=digest:raise SystemExit('SHA_MISMATCH:'+name)
    print('VERIFIED',name)
source=(root/'verify_066s_live_075.py').read_text(encoding='utf-8')
for banned in ('write_bytes(', 'write_text(', 'import subprocess', 'from subprocess', 'subprocess.run(', 'requests.', 'urllib.request', 'os.system(', 'os.popen('):
    if banned in source:raise SystemExit('FORBIDDEN_SIDE_EFFECT:'+banned)
print('BGXAI_075_SOURCE_ONLY_PASS',len(manifest['files']))
