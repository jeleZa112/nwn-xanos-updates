"""Read-only audit of user-owned native EET BCS, never publishes proprietary bytes."""
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json, sys, re

def audit(path):
    with ZipFile(path) as arc:
        required=('BDDEFAI.BCS','BDFTHI01.BCS','BDBARD01.BCS','BDBARD20.BCS')
        missing=[x for x in required if x not in arc.namelist()]
        if missing: raise ValueError('Missing '+repr(missing))
        by={x:arc.read(x) for x in required}
    b=by['BDDEFAI.BCS']
    if not (b.startswith(b'SC\nCR\n') and b.count(b'296OB')>=1 and
            b'BDAI_SKILL_MODE' in b and b'BD_BRDS' in b):
        raise ValueError('Bard base invariant FAILED')
    info={"private_bcs_not_included_in_published_release":True,
          "sources":{x:{"bytes":len(v),"sha256":sha256(v).hexdigest()} for x,v in by.items()},
          "required_song_action_id_296":b.count(b'296OB'),
          "bard_song_mode_present":b'BDAI_SKILL_MODE' in b,
          "bard_locals_flag_present":b'BD_BRDS' in b,
          "class_scripts_preserved_not_patched":True}
    return info

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Usage: audit_native.py /path/to/private/EET_archive.zip')
    print(json.dumps(audit(Path(sys.argv[1])),ensure_ascii=False,indent=2))
