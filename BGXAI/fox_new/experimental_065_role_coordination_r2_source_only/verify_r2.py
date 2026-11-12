"""Strict offline source-byte/hash check. Never touches the game or GitHub."""
import json
from hashlib import sha256
from pathlib import Path
ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT/'manifest_r2.json').read_text(encoding='utf-8'))
assert manifest['mode'] == 'SOURCE_ONLY'
for filename, meta in manifest['files'].items():
    data = (ROOT / filename).read_bytes()
    actual = sha256(data).hexdigest()
    assert len(data) == meta['size_bytes'], (filename, 'size mismatch')
    assert actual == meta['sha256'], (filename, 'sha mismatch')
print('BGXAI 065-R2 SOURCE VERIFIED', len(manifest['files']), 'files')
