import tempfile
from pathlib import Path
from verify_053_baseline import inspect,sha256_file

def ready(root):
    (root/'override').mkdir(parents=True)
    (root/'WeiDU.log').write_text('~BGX42/SETUP-BGX42.TP2~ #0 #0\n~BGX49/SETUP-BGX49.TP2~ #0 #0\n')
    (root/'chitin.key').write_bytes(b'key')
    paths={'override/BDDEFAI.BCS':b'game-bcs-blob',
           'override/M_BX43.lua':b'observer-lua',
           'override/M_BX44.lua':b'diag-lua'}
    for name,content in paths.items():
        (root/name).write_bytes(content)
    return {name:sha256_file(root/name) for name in paths}

def test_clean_exact_baseline():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); checks=ready(p)
        before={x.name:x.stat().st_mtime_ns for x in p.rglob('*') if x.is_file()}
        report=inspect(p,checks)
        after={x.name:x.stat().st_mtime_ns for x in p.rglob('*') if x.is_file()}
        assert report['verdict']=='BASELINE_OK_SOURCE_ONLY'
        assert report['writes_performed'] is False
        assert before==after

def test_mismatch_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); checks=ready(p)
        (p/'override/M_BX43.lua').write_bytes(b'unexpected edit')
        assert inspect(p,checks)['verdict']=='REVIEW_DO_NOT_INSTALL'

def test_other_mod_last_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); checks=ready(p)
        with (p/'WeiDU.log').open('a') as f:f.write('~EXTRAMOD/SETUP-EXTRAMOD.TP2~ #0 #0\n')
        assert 'BGX49_not_last_WeiDU_component' in inspect(p,checks)['issues']

def test_missing_game_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'does-not-exist'
        assert inspect(p)['verdict']=='REVIEW_DO_NOT_INSTALL'

def test_missing_chitin_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); checks=ready(p)
        (p/'chitin.key').unlink()
        assert 'chitin_key_missing' in inspect(p,checks)['issues']

def test_missing_observer_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);checks=ready(p)
        (p/'override/M_BX43.lua').unlink()
        assert inspect(p,checks)['verdict']=='REVIEW_DO_NOT_INSTALL'

def test_empty_WeiDU_blocks():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);checks=ready(p)
        (p/'WeiDU.log').write_text('garbage\n')
        assert inspect(p,checks)['verdict']=='REVIEW_DO_NOT_INSTALL'
