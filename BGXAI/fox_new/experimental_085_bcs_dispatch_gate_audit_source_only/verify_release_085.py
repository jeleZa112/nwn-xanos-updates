import hashlib,json,pathlib
p=pathlib.Path(__file__).parent
x=json.loads((p/'manifest_sha256.json').read_text('utf-8'))
for name,want in x['files'].items():
 if hashlib.sha256((p/name).read_bytes()).hexdigest()!=want:raise SystemExit('SHA_MISMATCH '+name)
s=(p/'BGXAI085_BCS_GATE_AUDIT.py').read_text('utf-8')
for bad in ('write_bytes(', 'write_text(', 'subprocess.', 'os.system(', 'virtual_InsertAction(', 'SetGlobal('):
 if bad in s:raise SystemExit('SOURCE_WRITE_TOKEN '+bad)
print('BGXAI085_SOURCE_ONLY_RELEASE_PASS',len(x['files']),'SHA256; NO_GAME_WRITE')
