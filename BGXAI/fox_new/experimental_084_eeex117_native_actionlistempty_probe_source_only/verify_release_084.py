import hashlib,json,pathlib
p=pathlib.Path(__file__).parent
m=json.loads((p/'manifest_sha256.json').read_text('utf-8'))
for f,digest in m['files'].items():
    have=hashlib.sha256((p/f).read_bytes()).hexdigest()
    if have!=digest: raise SystemExit('MISMATCH '+f)
source=(p/'BGXAI084_NATIVE_QUEUE_PROBE.lua').read_text('utf-8')
if 'safe_to_dispatch=true' in source or 'queue_empty_verified=true' in source:
    raise SystemExit('UNSAFE_PERMISSION_TOKEN')
if any(x in source for x in ('EEex_Action_AddSpriteStartedActionListener(', 'virtual_InsertAction(', 'SetGlobal(')):
    raise SystemExit('UNSAFE_ENGINE_WRITE_TOKEN')
print('BGXAI084_SOURCE_ONLY_RELEASE_PASS',len(m['files']),'SHA256; HOLD; NO_GAME_WRITE')
