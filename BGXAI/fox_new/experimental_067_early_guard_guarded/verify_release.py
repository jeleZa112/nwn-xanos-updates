"""Exact source bundle SHA256/byte-size verifier, excludes generated manifest itself."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).parent
MANIFEST=ROOT/'manifest.json'
def run():
 doc=json.loads(MANIFEST.read_text(encoding='utf-8'))
 for row in doc['files']:
  p=ROOT/row['path']
  if not p.is_file() or p.is_symlink():raise RuntimeError('SOURCE_MISSING_OR_LINK:'+row['path'])
  buf=p.read_bytes()
  if len(buf)!=row['size'] or hashlib.sha256(buf).hexdigest()!=row['sha256']:
   raise RuntimeError('SOURCE_HASH_OR_LENGTH_DRIFT:'+row['path'])
 return {'status':'067_SOURCE_MANIFEST_PASS','files':len(doc['files'])}
if __name__=='__main__':
 print(json.dumps(run(),ensure_ascii=False))
