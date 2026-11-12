from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
assert manifest['version']=='066S-GUARDED-064-BASELINE-SOURCE-ONLY'
assert len(manifest['files'])>=15
for meta in manifest['files']:
 p=root/meta['path'];assert p.is_file(),meta['path']
 raw=p.read_bytes()
 assert len(raw)==meta['size'],(meta['path'],'SIZE_MISMATCH')
 assert hashlib.sha256(raw).hexdigest()==meta['sha256'],(meta['path'],'SHA_MISMATCH')
print('BGXAI 066S MANIFEST PASS',len(manifest['files']))