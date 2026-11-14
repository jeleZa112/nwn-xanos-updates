"""Verify BGXAI071 source-only payload from current working directory; no game writes."""
import hashlib,json,re,sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
production=['BGXAI069_ROLE_OBSERVER.lua','BGXAI070_EEEX_FACTS_READONLY.lua',
            'BGXAI071_KIT_HINTS_READONLY.lua']
manifest=json.loads((ROOT/'manifest_sha256.json').read_text('utf-8'))
for name,digest in manifest['files'].items():
 data=(ROOT/name).read_bytes()
 if hashlib.sha256(data).hexdigest()!=digest:
  raise SystemExit(f'HASH_MISMATCH: {name}')
 print('SHA PASS',name)
for name in production:
 src=(ROOT/name).read_text('utf-8')
 for term in ('setLocalInt(', 'ClearActions(', 'AttackReevaluate(',
              'ProtectObject(', 'Spell(', ':Attack(', 'RegisterListener('):
  if term in src:
   raise SystemExit(f'ACTIVE_ACTION_BLOCKED: {name} {term}')
 print('PASSIVE_ONLY PASS',name)
print('BGXAI071_SOURCE_ONLY_VERIFIED',len(manifest['files']),'files')
