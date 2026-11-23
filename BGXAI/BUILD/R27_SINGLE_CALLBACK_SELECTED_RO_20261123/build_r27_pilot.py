"""Source-only staging, NOT installer, for separate future typed-authorized WeiDU."""
from pathlib import Path
from build_r27 import ROOT, compose, sha

RESOURCE = 'M_BGXR27'  # exact 8 chars for engine resref

def make(root: Path=ROOT)->bytes:
    assert len(RESOURCE)==8
    original=compose(root)
    suffix=b'return R27\n'
    if not original.endswith(suffix):raise ValueError('EXPECTED_R27_EXPORT_MISSING')
    bootstrap=(root/'R27_AUTHORIZED_PILOT_BOOTSTRAP.lua').read_bytes()
    if b'P.initialized=start()' not in bootstrap:
        raise ValueError('BOOTSTRAP_NOT_AUTO_STARTING_AFTER_AUTHORIZED_INSTALL')
    return original[:-len(suffix)]+bootstrap

if __name__=='__main__':
    p=ROOT/(RESOURCE+'.lua')
    p.write_bytes(make())
    print(p.name,p.stat().st_size,sha(p.read_bytes()))
