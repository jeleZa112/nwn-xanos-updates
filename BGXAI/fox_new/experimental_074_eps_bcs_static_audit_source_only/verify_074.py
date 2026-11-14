#!/usr/bin/env python3
"""Fail closed on source-only package file hash mismatch. No game I/O."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest_sha256.json').read_text(encoding='utf-8'))
for n,d in sorted(m['files'].items()):
    if '/' in n or '\\' in n or n.startswith('.'):
        raise SystemExit('UNSAFE_MANIFEST_PATH')
    b=(p/n).read_bytes()
    if hashlib.sha256(b).hexdigest()!=d:
        raise SystemExit(f'FAILED_SHA256:{n}')
    print('VERIFIED',n)
if any(x.suffix.lower()=='.bcs' for x in p.rglob('*')):
    raise SystemExit('PRIVATE_BCS_MUST_NOT_BE_IN_SOURCE_PACKAGE')
print('BGXAI_074_STATIC_SOURCE_ONLY_PASS',len(m['files']))
