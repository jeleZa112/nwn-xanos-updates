"""Read-only SHA verifier for BGXAI072 SOURCE ONLY."""
import pathlib,hashlib,json
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'manifest_sha256.json').read_text('utf-8'))
for name,hash_ in manifest['files'].items():
 data=(root/name).read_bytes()
 if hashlib.sha256(data).hexdigest()!=hash_:
  raise SystemExit('SHA_MISMATCH '+name)
 print('SHA_PASS',name)
src=(root/'BGXAI072_EPS_FIRST_ARBITER.lua').read_text('utf-8')
for forbidden in ('setLocalInt(',':Attack(', 'AttackReevaluate(', 'Spell(',
                  'ClearActions(', 'ProtectObject(', 'EEex_Sprite_Add'):
 if forbidden in src:raise SystemExit('GAME_ACTION_NOT_PASSIVE '+forbidden)
print('BGXAI072_SOURCE_ONLY_VERIFIED')
